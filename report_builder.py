"""Build concise Chinese daily market reports from market data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import re
from statistics import mean
from typing import Optional


@dataclass(frozen=True)
class AssetQuote:
    ticker: str
    name: str
    group_key: str
    group_title: str
    close: Optional[float] = None
    pct_change: Optional[float] = None
    date: Optional[date] = None
    display_divisor: float = 1.0
    display_suffix: str = ""
    source: str = ""


def quote_from_bars(asset: dict, bars, source_name: str) -> AssetQuote:
    if len(bars) < 1:
        return AssetQuote(
            ticker=asset["ticker"],
            name=asset["name"],
            group_key=asset["group_key"],
            group_title=asset["group_title"],
            source=source_name,
            display_divisor=float(asset.get("display_divisor", 1)),
            display_suffix=asset.get("display_suffix", ""),
        )

    latest = bars[-1]
    pct_change = None
    if len(bars) >= 2 and bars[-2].close:
        pct_change = (latest.close / bars[-2].close - 1) * 100

    return AssetQuote(
        ticker=asset["ticker"],
        name=asset["name"],
        group_key=asset["group_key"],
        group_title=asset["group_title"],
        close=latest.close,
        pct_change=pct_change,
        date=latest.date,
        display_divisor=float(asset.get("display_divisor", 1)),
        display_suffix=asset.get("display_suffix", ""),
        source=source_name,
    )


def build_report(quotes: list[AssetQuote], report_date: Optional[date], model_analysis: Optional[dict] = None) -> str:
    if not report_date:
        return "【美股收盘简报｜无交易数据】\n\n昨日美股休市/无交易数据。7 天内未获取到核心 ETF 有效收盘数据。"

    lines = [f"【美股收盘简报｜{report_date.isoformat()}】", ""]
    grouped = defaultdict(list)
    for quote in quotes:
        grouped[quote.group_key].append(quote)

    lines.extend(_build_core_section(grouped["core"]))
    lines.append("")
    lines.extend(_build_macro_section(grouped["macro"]))
    lines.append("")
    lines.extend(_build_sector_section(grouped, model_analysis=model_analysis))
    lines.append("")
    lines.extend(_build_market_view(grouped, model_analysis=model_analysis))
    lines.append("")
    lines.extend(_build_watch_points(grouped, model_analysis=model_analysis))
    return "\n".join(lines)


def _format_pct(value: Optional[float]) -> str:
    if value is None:
        return "涨跌幅缺失"
    text = f"{value:+.2f}%"
    if value > 0:
        return f'<font color="green">{text}</font>'
    if value < 0:
        return f'<font color="red">{text}</font>'
    return text


def _format_quote(quote: AssetQuote) -> str:
    if quote.close is None:
        return f"- **{quote.ticker}**：数据缺失"
    price = _format_price(quote)
    return f"- **{quote.ticker}**：{price} ｜ {_format_pct(quote.pct_change)}"


def _format_price(quote: AssetQuote) -> str:
    if quote.close is None:
        return "数据缺失"
    value = _display_value(quote)
    suffix = quote.display_suffix
    return f"{value:.2f}{suffix}"


def _display_value(quote: AssetQuote) -> float:
    if quote.ticker == "^TNX" and quote.close is not None:
        return quote.close / 10 if quote.close > 20 else quote.close
    return (quote.close or 0) / quote.display_divisor


def _build_core_section(quotes: list[AssetQuote]) -> list[str]:
    return ["**一、核心指数 / ETF**"] + [_format_quote_row(quote, include_price=True) for quote in quotes]


def _build_macro_section(quotes: list[AssetQuote]) -> list[str]:
    return ["**二、宏观 / 风险**"] + [_format_quote(quote) for quote in quotes]


def _build_sector_section(grouped, model_analysis: Optional[dict] = None) -> list[str]:
    section = ["**三、板块观察**"]
    for key in ("ai_semis", "ai_power", "commodities"):
        quotes = grouped[key]
        title = grouped[key][0].group_title if grouped[key] else key
        section.append("")
        if not quotes:
            section.append(f"**{title}**\n- 数据缺失")
            continue
        section.append(f"**{title}**")
        section.extend(_format_quote_row(quote) for quote in quotes)
    if model_analysis and model_analysis.get("sector_insights"):
        section.append("")
        section.append("**板块洞察**")
        for item in model_analysis["sector_insights"][:3]:
            sector = item.get("sector", "").strip()
            insight = item.get("insight", "").strip()
            if sector and insight:
                section.append(f"- **{sector}**：{insight}")
    return section


def _format_quote_row(quote: AssetQuote, include_price: bool = False) -> str:
    if quote.close is None:
        return f"- **{quote.ticker}** ｜ 数据缺失"
    if include_price:
        return f"- **{quote.ticker}** ｜ 收盘 {_format_price(quote)} ｜ {_format_pct(quote.pct_change)}"
    return f"- **{quote.ticker}** ｜ {_format_pct(quote.pct_change)}"


def _build_market_view(grouped, model_analysis: Optional[dict] = None) -> list[str]:
    qqq = _find(grouped["core"], "QQQ")
    voo = _find(grouped["core"], "VOO")
    smh = _find(grouped["core"], "SMH")
    vix = _find(grouped["macro"], "^VIX")
    tnx = _find(grouped["macro"], "^TNX")

    facts = []
    for quote in (qqq, voo, smh, vix):
        if quote and quote.pct_change is not None:
            facts.append(f"{quote.ticker} {_format_pct(quote.pct_change)}")
    if tnx and tnx.close is not None:
        facts.append(f"10Y 美债约 {_display_value(tnx):.2f}%")

    model_label = "非模型结果"
    model_view = _infer_market_view(qqq, voo, smh, vix, tnx)
    if model_analysis:
        model_label = model_analysis.get("label") or model_label
        model_view = model_analysis.get("market_view") or model_view
        model_view = _strip_model_prefix(model_view)
    lines = [
        "**四、模型分析**",
        "**数据事实**：" + ("，".join(facts) + "。" if facts else "核心数据不足。"),
        "",
        f"**{model_label}**：",
        model_view,
    ]
    if model_analysis and model_analysis.get("macro_fund_flows"):
        lines.extend(["", "**宏观/资金面**："])
        lines.extend(f"- {item}" for item in model_analysis["macro_fund_flows"][:5])
    if model_analysis and model_analysis.get("investment_advice"):
        lines.extend(["", "**投资建议**：" + model_analysis["investment_advice"]])
    return lines


def _strip_model_prefix(text: str) -> str:
    cleaned = text.strip()
    for prefix in ("【模型判断】", "[模型判断]", "模型判断：", "模型判断:", "判断：", "判断:"):
        if cleaned.startswith(prefix):
            return cleaned[len(prefix) :].strip()
    return cleaned


def _strip_observation_label(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^【([^】]{1,18})[：:·][^】]{1,18}】\s*", r"**\1**：", cleaned)
    cleaned = re.sub(r"^【([^】]{1,18})】\s*", r"**\1**：", cleaned)
    return cleaned


def _infer_market_view(qqq, voo, smh, vix, tnx) -> str:
    risk_on_score = 0
    if qqq and qqq.pct_change is not None:
        risk_on_score += 1 if qqq.pct_change > 0 else -1
    if voo and voo.pct_change is not None:
        risk_on_score += 1 if voo.pct_change > 0 else -1
    if smh and smh.pct_change is not None:
        risk_on_score += 1 if smh.pct_change > 0 else -1
    if vix and vix.pct_change is not None:
        risk_on_score += 1 if vix.pct_change < 0 else -1

    if risk_on_score >= 3:
        return "昨夜偏风险偏好修复，科技和半导体表现较强，波动率变化对成长股相对友好。"
    if risk_on_score <= -3:
        return "昨夜偏风险偏好降温，主要指数和成长方向承压，需要观察波动率与利率是否继续上行。"
    return "昨夜市场表现偏分化，指数、波动率和半导体方向没有形成单边一致信号。"


def _build_watch_points(grouped, model_analysis: Optional[dict] = None) -> list[str]:
    if model_analysis and model_analysis.get("watch_points"):
        return ["**五、下一交易日观察重点**"] + [
            f"- {point}" for point in model_analysis["watch_points"][:5]
        ]

    qqq = _find(grouped["core"], "QQQ")
    voo = _find(grouped["core"], "VOO")
    vix = _find(grouped["macro"], "^VIX")
    tnx = _find(grouped["macro"], "^TNX")
    semis_avg = _average_pct(grouped["ai_semis"])
    power_avg = _average_pct(grouped["ai_power"])

    trend_line = "- 观察 QQQ/VOO 是否延续当前趋势"
    if _is_positive(qqq) and _is_positive(voo):
        trend_line = "- 观察 QQQ/VOO 能否延续反弹，确认大盘风险偏好是否继续修复"
    elif _is_negative(qqq) and _is_negative(voo):
        trend_line = "- 观察 QQQ/VOO 能否止跌，确认大盘压力是否缓和"

    macro_line = "- 观察 VIX 和 10Y 美债变化对风险资产的影响"
    vix_down = vix and vix.pct_change is not None and vix.pct_change < 0
    vix_up = vix and vix.pct_change is not None and vix.pct_change > 0
    tnx_up = tnx and tnx.pct_change is not None and tnx.pct_change > 0
    tnx_down = tnx and tnx.pct_change is not None and tnx.pct_change < 0
    if vix_down and tnx_down:
        macro_line = "- 观察 VIX 和 10Y 美债是否继续回落，给成长股提供支撑"
    elif vix_up or tnx_up:
        macro_line = "- 观察 VIX 或 10Y 美债是否继续上行，重新压制风险资产"
    elif vix_down:
        macro_line = "- 观察 VIX 回落能否延续，风险偏好是否继续改善"

    sector_line = "- 观察 AI 半导体和 AI 电力是否继续分化"
    if semis_avg is not None and power_avg is not None:
        spread = semis_avg - power_avg
        if abs(spread) < 0.75:
            sector_line = "- 观察 AI 半导体和 AI 电力能否同步走强，而不是重新分化"
        elif spread > 0:
            sector_line = "- 观察 AI 半导体相对 AI 电力的强势能否延续"
        else:
            sector_line = "- 观察 AI 电力相对 AI 半导体的强势能否延续"

    return [
        "**五、下一交易日观察重点**",
        trend_line,
        macro_line,
        sector_line,
    ]


def _average_pct(quotes: list[AssetQuote]) -> Optional[float]:
    values = [quote.pct_change for quote in quotes if quote.pct_change is not None]
    if not values:
        return None
    return mean(values)


def _is_positive(quote: Optional[AssetQuote]) -> bool:
    return bool(quote and quote.pct_change is not None and quote.pct_change > 0)


def _is_negative(quote: Optional[AssetQuote]) -> bool:
    return bool(quote and quote.pct_change is not None and quote.pct_change < 0)


def _find(quotes: list[AssetQuote], ticker: str) -> Optional[AssetQuote]:
    for quote in quotes:
        if quote.ticker == ticker:
            return quote
    return None
