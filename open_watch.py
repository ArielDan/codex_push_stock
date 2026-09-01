"""US market open +30 minute watch report generation."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import json
import logging
import os
from pathlib import Path
from typing import Optional

from config import all_assets, load_asset_groups
from data_sources import PolygonSource, YFinanceSource
from market_calendar import CHINA_TZ, NY_TZ, open_watch_window_status, previous_trading_day
from technical_analysis import TechnicalSnapshot, build_snapshot


logger = logging.getLogger(__name__)
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "open_watch"


def check_window_text(now: Optional[datetime] = None) -> str:
    status = open_watch_window_status(now or datetime.now(CHINA_TZ))
    lines = [
        f"当前纽约时间：{status.ny_now.isoformat()}",
        f"美股交易日：{'是' if status.is_trading_day else '否'}",
        f"开盘30分钟观察窗口：{status.window_start.isoformat()} ~ {status.window_end.isoformat()}",
        f"当前是否在窗口内：{'是' if status.in_window else '否'}",
    ]
    return "\n".join(lines)


def should_run_open_watch(now: Optional[datetime] = None) -> tuple[bool, str, date]:
    status = open_watch_window_status(now or datetime.now(CHINA_TZ))
    if not status.is_trading_day:
        return False, "当前纽约日期不是美股交易日，已跳过开盘观察。", previous_trading_day(status.session_date)
    if not status.in_window:
        return False, "当前纽约时间不在开盘30分钟观察窗口，已跳过飞书推送。", status.session_date
    return True, "当前处于开盘30分钟观察窗口。", status.session_date


def generate_open_watch_report(now: Optional[datetime] = None) -> dict:
    generated_at = now or datetime.now(CHINA_TZ)
    status = open_watch_window_status(generated_at)
    session_date = status.session_date if status.is_trading_day else previous_trading_day(status.session_date)
    snapshots, limitations = _fetch_snapshots(session_date, generated_at)
    return _build_report_json(session_date, generated_at, snapshots, limitations)


def write_open_watch_outputs(report: dict) -> None:
    reports_dir = OUTPUT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_text = report["date"]
    _write_json(OUTPUT_DIR / "latest.json", report)
    _write_json(reports_dir / f"{date_text}.json", report)
    _write_json(OUTPUT_DIR / "index.json", _updated_index(date_text, report))


def build_open_watch_feishu_report(report: dict) -> str:
    lines = [f"【美股开盘30分钟观察｜{report['date']}】", ""]
    lines.extend(_market_overview_lines(report))
    lines.append("")
    lines.extend(_style_lines(report))
    lines.append("")
    lines.extend(_technical_lines(report))
    lines.append("")
    lines.extend(_ranking_lines(report))
    lines.append("")
    lines.extend(["**五、一句话结论**", report["summary"].get("one_sentence") or "开盘数据不足，先观察。"])
    lines.append("")
    lines.extend(["**六、今日观察重点**"])
    for point in report.get("watch_points") or []:
        lines.append(f"- {point}")
    if report.get("limitations"):
        lines.append("")
        lines.append("**数据限制**")
        for item in report["limitations"][:5]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _fetch_snapshots(session_date: date, generated_at: datetime) -> tuple[list[TechnicalSnapshot], list[str]]:
    sources = _build_sources()
    snapshots: list[TechnicalSnapshot] = []
    limitations: list[str] = []
    for asset in all_assets():
        snapshot = None
        last_error = None
        for source in sources:
            try:
                intraday_bars = source.get_intraday_bars(asset["ticker"], session_date, interval="1m")
                previous_close = _previous_close(source, asset["ticker"], session_date)
                snapshot = build_snapshot(asset, intraday_bars, previous_close, session_date, generated_at, source.name)
                if snapshot.price is not None:
                    break
                last_error = RuntimeError(f"{source.name} 盘中数据不足")
            except Exception as exc:
                last_error = exc
                logger.warning("%s 使用 %s 拉取盘中数据失败：%s", asset["ticker"], source.name, exc)
        if snapshot is None:
            snapshot = build_snapshot(asset, [], None, session_date, generated_at, sources[-1].name)
        if snapshot.price is None:
            limitations.append(f"{asset['ticker']} 数据缺失：{last_error}")
        snapshots.append(snapshot)
    return snapshots, limitations


def _build_sources():
    fallback = YFinanceSource()
    if os.getenv("POLYGON_API_KEY"):
        try:
            return [PolygonSource(), fallback]
        except Exception as exc:
            logger.warning("Polygon 初始化失败，将使用 yfinance：%s", exc)
    return [fallback]


def _previous_close(source, ticker: str, session_date: date) -> Optional[float]:
    bars = source.get_daily_bars(ticker, 7)
    previous = [bar.close for bar in bars if bar.date < session_date]
    return previous[-1] if previous else None


def _build_report_json(
    session_date: date,
    generated_at: datetime,
    snapshots: list[TechnicalSnapshot],
    limitations: list[str],
) -> dict:
    overview = [_snapshot_to_dict(snapshot) for snapshot in snapshots]
    groups = _grouped_assets(overview)
    rankings = _rankings(overview)
    summary = _summary(overview)
    return {
        "date": session_date.isoformat(),
        "generated_at": generated_at.astimezone(CHINA_TZ).isoformat(),
        "market_session": "open_30min",
        "summary": summary,
        "overview": overview,
        "groups": groups,
        "rankings": rankings,
        "watch_points": _watch_points(summary, rankings, overview),
        "limitations": limitations,
    }


def _snapshot_to_dict(snapshot: TechnicalSnapshot) -> dict:
    return {
        "ticker": snapshot.ticker,
        "name": snapshot.name,
        "group_key": snapshot.group_key,
        "group_title": snapshot.group_title,
        "price": _display_value(snapshot.ticker, snapshot.price),
        "day_change_pct": _round(snapshot.day_change_pct),
        "open_30m_change_pct": _round(snapshot.open_30m_change_pct),
        "open_price": _display_value(snapshot.ticker, snapshot.open_price),
        "opening_range_high": _display_value(snapshot.ticker, snapshot.opening_range_high),
        "opening_range_low": _display_value(snapshot.ticker, snapshot.opening_range_low),
        "vwap": _display_value(snapshot.ticker, snapshot.vwap),
        "vwap_position": snapshot.vwap_position,
        "opening_range_position": snapshot.opening_range_position,
        "trend_label": snapshot.trend_label,
        "observation": snapshot.observation,
        "data_source": snapshot.data_source,
        "display_suffix": snapshot.display_suffix,
    }


def _grouped_assets(overview: list[dict]) -> dict:
    by_key = defaultdict(list)
    for item in overview:
        by_key[item["group_key"]].append(item)

    groups = {}
    for group in load_asset_groups():
        groups[group["key"]] = {
            "title": group["title"],
            "assets": by_key.get(group["key"], []),
        }
    return groups


def _rankings(overview: list[dict]) -> dict:
    valid = [item for item in overview if item.get("open_30m_change_pct") is not None]
    sorted_valid = sorted(valid, key=lambda item: item["open_30m_change_pct"], reverse=True)
    qqq = _find(overview, "QQQ")
    qqq_change = qqq.get("open_30m_change_pct") if qqq else None
    relative = []
    if qqq_change is not None:
        for item in valid:
            if item["ticker"] == "QQQ":
                continue
            relative.append({**item, "relative_to_qqq_pct": _round(item["open_30m_change_pct"] - qqq_change)})
        relative.sort(key=lambda item: item["relative_to_qqq_pct"], reverse=True)
    return {
        "top_gainers": sorted_valid[:3],
        "top_losers": sorted(valid, key=lambda item: item["open_30m_change_pct"])[:3],
        "relative_strong_vs_qqq": relative[:3],
        "relative_weak_vs_qqq": list(reversed(relative[-3:])) if relative else [],
    }


def _summary(overview: list[dict]) -> dict:
    qqq = _find(overview, "QQQ")
    voo = _find(overview, "VOO")
    iwm = _find(overview, "IWM")
    smh = _find(overview, "SMH")
    soxx = _find(overview, "SOXX")
    vix = _find(overview, "^VIX")
    tnx = _find(overview, "^TNX")
    risk = _risk_appetite(qqq, voo, iwm, vix)
    tech = _strength_label([qqq, voo])
    semis = _strength_label([smh, soxx])
    small_caps = "strong" if _change(iwm) and _change(iwm) > 0 else "weak"
    rate_pressure = "neutral"
    if _change(tnx) is not None:
        rate_pressure = "up" if _change(tnx) > 0 else "down" if _change(tnx) < 0 else "neutral"
    return {
        "one_sentence": _one_sentence(risk, tech, semis, small_caps, rate_pressure),
        "risk_appetite": risk,
        "tech_growth": tech,
        "semiconductor": semis,
        "small_caps": small_caps,
        "rate_pressure": rate_pressure,
    }


def _risk_appetite(qqq, voo, iwm, vix) -> str:
    score = 0
    for item in (qqq, voo, iwm):
        change = _change(item)
        if change is not None:
            score += 1 if change > 0 else -1
    vix_change = _change(vix)
    if vix_change is not None:
        score += 1 if vix_change < 0 else -1
    if score >= 2:
        return "strong"
    if score <= -2:
        return "weak"
    return "neutral"


def _strength_label(items: list[Optional[dict]]) -> str:
    changes = [_change(item) for item in items if _change(item) is not None]
    if not changes:
        return "mixed"
    positives = sum(1 for change in changes if change > 0)
    if positives == len(changes):
        return "strong"
    if positives == 0:
        return "weak"
    return "mixed"


def _one_sentence(risk: str, tech: str, semis: str, small_caps: str, rate_pressure: str) -> str:
    risk_text = {"strong": "风险偏好偏强", "neutral": "风险偏好中性", "weak": "风险偏好偏弱"}[risk]
    tech_text = {"strong": "科技成长走强", "mixed": "科技成长分化", "weak": "科技成长承压"}[tech]
    semi_text = {"strong": "半导体走强", "mixed": "半导体分化", "weak": "半导体承压"}[semis]
    small_caps_text = {"strong": "偏强", "weak": "偏弱"}.get(small_caps, "未知")
    rate_text = {"up": "利率压力上行", "down": "利率压力缓和", "neutral": "利率压力中性"}[rate_pressure]
    return f"开盘30分钟显示{risk_text}，{tech_text}，{semi_text}，小盘股{small_caps_text}，{rate_text}。"


def _watch_points(summary: dict, rankings: dict, overview: list[dict]) -> list[str]:
    points = [
        "观察 QQQ 是否站稳 VWAP 及开盘30分钟高点，确认科技成长动能是延续还是冲高回落。",
        "观察 SMH/SOXX 与半导体个股是否同向，若 ETF 强而龙头弱，说明板块内部承接仍需验证。",
        "观察 VIX 与 10Y 美债收益率是否同向压制风险资产，避免把单个 ticker 异动误读成全面趋势。",
    ]
    strong = rankings.get("relative_strong_vs_qqq") or []
    weak = rankings.get("relative_weak_vs_qqq") or []
    if strong:
        points.append(f"相对 QQQ 强势资产先看 {', '.join(item['ticker'] for item in strong[:3])}，观察强势能否在指数震荡时保持。")
    if weak:
        points.append(f"相对 QQQ 弱势资产先看 {', '.join(item['ticker'] for item in weak[:3])}，若无法收回 VWAP，短线偏弱。")
    return points[:5]


def _market_overview_lines(report: dict) -> list[str]:
    overview = report["overview"]
    lines = ["**一、市场总览**"]
    for ticker in ("QQQ", "VOO", "DIA", "IWM"):
        lines.append(_overview_line(overview, ticker))
    smh = _find(overview, "SMH")
    soxx = _find(overview, "SOXX")
    lines.append(f"- **SMH / SOXX**：{_brief_asset(smh)} / {_brief_asset(soxx)}")
    lines.append(_overview_line(overview, "^VIX", "VIX"))
    lines.append(_overview_line(overview, "^TNX", "10Y美债"))
    lines.append(_overview_line(overview, "DX-Y.NYB", "美元指数"))
    return lines


def _style_lines(report: dict) -> list[str]:
    summary = report["summary"]
    return [
        "**二、开盘风格判断**",
        f"- **风险偏好**：{_style_text(summary.get('risk_appetite'))}",
        f"- **科技成长**：{_style_text(summary.get('tech_growth'))}",
        f"- **半导体**：{_style_text(summary.get('semiconductor'))}",
        f"- **小盘股**：{_style_text(summary.get('small_caps'))}",
        f"- **利率压力**：{_style_text(summary.get('rate_pressure'))}",
    ]


def _technical_lines(report: dict) -> list[str]:
    lines = ["**三、重点资产技术走势**"]
    for group_key, group in report["groups"].items():
        assets = group.get("assets") or []
        if not assets:
            continue
        lines.append("")
        lines.append(f"**{group['title']}**")
        for item in assets:
            lines.extend(_asset_technical_block(item))
    return lines


def _asset_technical_block(item: dict) -> list[str]:
    if item.get("price") is None:
        return [f"- **{item['ticker']}**：数据缺失"]
    key_position = (
        f"VWAP {_position_text(item.get('vwap_position'))}，"
        f"区间 {_range_text(item.get('opening_range_position'))}"
    )
    return [
        f"- **{item['ticker']}**：{_fmt_price(item)}，日内 {_fmt_pct(item.get('day_change_pct'))}，开盘30m {_fmt_pct(item.get('open_30m_change_pct'))}，{item.get('trend_label')}",
        f"  关键位置：{key_position}；开盘 {_fmt_number(item.get('open_price'), item.get('display_suffix'))}，高 {_fmt_number(item.get('opening_range_high'), item.get('display_suffix'))}，低 {_fmt_number(item.get('opening_range_low'), item.get('display_suffix'))}",
        f"  观察动作：{item.get('observation')}",
    ]


def _ranking_lines(report: dict) -> list[str]:
    rankings = report["rankings"]
    return [
        "**四、强弱榜**",
        f"- **开盘30分钟涨幅前三**：{_ranking_text(rankings.get('top_gainers'))}",
        f"- **开盘30分钟跌幅前三**：{_ranking_text(rankings.get('top_losers'))}",
        f"- **相对 QQQ 强势**：{_ranking_text(rankings.get('relative_strong_vs_qqq'), 'relative_to_qqq_pct')}",
        f"- **相对 QQQ 弱势**：{_ranking_text(rankings.get('relative_weak_vs_qqq'), 'relative_to_qqq_pct')}",
    ]


def _overview_line(overview: list[dict], ticker: str, label: Optional[str] = None) -> str:
    item = _find(overview, ticker)
    return f"- **{label or ticker}**：{_brief_asset(item)}"


def _brief_asset(item: Optional[dict]) -> str:
    if not item or item.get("price") is None:
        return "数据缺失"
    return f"{_fmt_price(item)}，{_fmt_pct(item.get('day_change_pct'))}，30m {_fmt_pct(item.get('open_30m_change_pct'))}"


def _ranking_text(items: Optional[list[dict]], field: str = "open_30m_change_pct") -> str:
    if not items:
        return "无有效数据"
    return "，".join(f"{item['ticker']} {_fmt_pct(item.get(field))}" for item in items)


def _style_text(value: Optional[str]) -> str:
    mapping = {
        "strong": "偏强",
        "neutral": "中性",
        "weak": "偏弱",
        "mixed": "分化",
        "up": "上行",
        "down": "下行",
    }
    return mapping.get(value or "", value or "未知")


def _position_text(value: Optional[str]) -> str:
    return {
        "above": "上方",
        "below": "下方",
        "near": "附近",
        "unknown": "未知",
    }.get(value or "unknown", "未知")


def _range_text(value: Optional[str]) -> str:
    return {
        "near_high": "接近高点",
        "middle": "中部",
        "near_low": "接近低点",
        "breakout_up": "向上突破",
        "breakdown_down": "向下跌破",
        "unknown": "未知",
    }.get(value or "unknown", "未知")


def _find(overview: list[dict], ticker: str) -> Optional[dict]:
    for item in overview:
        if item.get("ticker") == ticker:
            return item
    return None


def _change(item: Optional[dict]) -> Optional[float]:
    if not item:
        return None
    return item.get("open_30m_change_pct")


def _fmt_price(item: dict) -> str:
    return _fmt_number(item.get("price"), item.get("display_suffix"))


def _fmt_number(value: Optional[float], suffix: str = "") -> str:
    if value is None:
        return "缺失"
    return f"{value:.2f}{suffix or ''}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "缺失"
    return f"{value:+.2f}%"


def _display_value(ticker: str, value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if ticker == "^TNX" and value > 20:
        return _round(value / 10)
    return _round(value)


def _round(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 4)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _updated_index(date_text: str, report: dict) -> dict:
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = {"reports": []}
    else:
        index = {"reports": []}

    reports = [item for item in index.get("reports", []) if item.get("date") != date_text]
    reports.insert(
        0,
        {
            "date": date_text,
            "generated_at": report["generated_at"],
            "path": f"reports/{date_text}.json",
            "one_sentence": report["summary"].get("one_sentence", ""),
        },
    )
    return {"reports": reports[:60]}
