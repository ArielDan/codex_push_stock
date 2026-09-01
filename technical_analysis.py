"""Technical calculations for the US open +30 minute watch report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

from data_sources import IntradayBar


NY_TZ = ZoneInfo("America/New_York")
REGULAR_OPEN = time(9, 30)
OPEN_RANGE_END = time(10, 0)
VWAP_NEAR_THRESHOLD = 0.002
RANGE_NEAR_THRESHOLD = 0.2


@dataclass(frozen=True)
class TechnicalSnapshot:
    ticker: str
    name: str
    group_key: str
    group_title: str
    price: Optional[float]
    day_change_pct: Optional[float]
    open_30m_change_pct: Optional[float]
    open_price: Optional[float]
    opening_range_high: Optional[float]
    opening_range_low: Optional[float]
    vwap: Optional[float]
    vwap_position: str
    opening_range_position: str
    trend_label: str
    observation: str
    data_source: str = ""
    display_suffix: str = ""


def build_snapshot(
    asset: dict,
    bars: list[IntradayBar],
    previous_close: Optional[float],
    session_date: date,
    generated_at: datetime,
    source_name: str,
) -> TechnicalSnapshot:
    usable_bars = _regular_session_bars(bars, session_date, generated_at)
    if len(usable_bars) < 2:
        return _missing_snapshot(asset, source_name)

    opening_bars = [
        bar for bar in usable_bars if REGULAR_OPEN <= bar.timestamp.astimezone(NY_TZ).time() <= OPEN_RANGE_END
    ]
    if len(opening_bars) < 2:
        return _missing_snapshot(asset, source_name)

    first = opening_bars[0]
    latest = usable_bars[-1]
    open_price = first.open
    range_high = max(bar.high for bar in opening_bars)
    range_low = min(bar.low for bar in opening_bars)
    vwap = _vwap(usable_bars)
    day_change_pct = _pct_change(latest.close, previous_close)
    open_30m_change_pct = _pct_change(latest.close, open_price)
    vwap_position = _vwap_position(latest.close, vwap)
    range_position = _opening_range_position(latest.close, range_high, range_low)
    trend_label = _trend_label(latest.close, open_price, vwap_position, range_position, open_30m_change_pct)
    observation = _observation(trend_label, vwap_position, range_position)

    return TechnicalSnapshot(
        ticker=asset["ticker"],
        name=asset.get("name", asset["ticker"]),
        group_key=asset["group_key"],
        group_title=asset["group_title"],
        price=latest.close,
        day_change_pct=day_change_pct,
        open_30m_change_pct=open_30m_change_pct,
        open_price=open_price,
        opening_range_high=range_high,
        opening_range_low=range_low,
        vwap=vwap,
        vwap_position=vwap_position,
        opening_range_position=range_position,
        trend_label=trend_label,
        observation=observation,
        data_source=source_name,
        display_suffix=asset.get("display_suffix", ""),
    )


def _missing_snapshot(asset: dict, source_name: str) -> TechnicalSnapshot:
    return TechnicalSnapshot(
        ticker=asset["ticker"],
        name=asset.get("name", asset["ticker"]),
        group_key=asset["group_key"],
        group_title=asset["group_title"],
        price=None,
        day_change_pct=None,
        open_30m_change_pct=None,
        open_price=None,
        opening_range_high=None,
        opening_range_low=None,
        vwap=None,
        vwap_position="unknown",
        opening_range_position="unknown",
        trend_label="数据不足",
        observation="数据不足，暂不做技术判断。",
        data_source=source_name,
        display_suffix=asset.get("display_suffix", ""),
    )


def _regular_session_bars(bars: list[IntradayBar], session_date: date, generated_at: datetime) -> list[IntradayBar]:
    ny_generated_at = generated_at.astimezone(NY_TZ)
    filtered = []
    for bar in sorted(bars, key=lambda item: item.timestamp):
        timestamp = bar.timestamp.astimezone(NY_TZ)
        if timestamp.date() != session_date:
            continue
        if timestamp.time() < REGULAR_OPEN:
            continue
        if timestamp > ny_generated_at:
            continue
        filtered.append(bar)
    return filtered


def _pct_change(current: Optional[float], base: Optional[float]) -> Optional[float]:
    if current is None or base in (None, 0):
        return None
    return (current / base - 1) * 100


def _vwap(bars: list[IntradayBar]) -> Optional[float]:
    weighted = 0.0
    total_volume = 0.0
    for bar in bars:
        volume = max(float(bar.volume or 0), 0)
        typical = (bar.high + bar.low + bar.close) / 3
        weighted += typical * volume
        total_volume += volume
    if total_volume <= 0:
        return None
    return weighted / total_volume


def _vwap_position(price: Optional[float], vwap: Optional[float]) -> str:
    if price is None or vwap in (None, 0):
        return "unknown"
    distance = price / vwap - 1
    if abs(distance) <= VWAP_NEAR_THRESHOLD:
        return "near"
    return "above" if distance > 0 else "below"


def _opening_range_position(price: Optional[float], high: Optional[float], low: Optional[float]) -> str:
    if price is None or high is None or low is None or high <= low:
        return "unknown"
    if price > high:
        return "breakout_up"
    if price < low:
        return "breakdown_down"
    percentile = (price - low) / (high - low)
    if percentile >= 1 - RANGE_NEAR_THRESHOLD:
        return "near_high"
    if percentile <= RANGE_NEAR_THRESHOLD:
        return "near_low"
    return "middle"


def _trend_label(
    price: float,
    open_price: float,
    vwap_position: str,
    range_position: str,
    open_30m_change_pct: Optional[float],
) -> str:
    change = open_30m_change_pct or 0
    if range_position == "breakout_up" or (change >= 0.6 and vwap_position == "above"):
        return "强势上攻"
    if range_position == "breakdown_down" or (change <= -0.8 and vwap_position == "below"):
        return "放量下跌"
    if price < open_price and change < -0.2:
        return "高开回落"
    if price > open_price and change > 0.2 and vwap_position in {"near", "above"}:
        return "低开修复"
    return "横盘震荡"


def _observation(trend_label: str, vwap_position: str, range_position: str) -> str:
    if trend_label == "强势上攻":
        return "若价格继续站上 VWAP 且突破开盘 30 分钟高点，可观察顺势动能是否延续。"
    if trend_label == "放量下跌":
        return "若跌破 VWAP 且无法收回，短线偏弱，避免追高，观察是否继续跌破开盘低点。"
    if trend_label == "高开回落":
        return "若高开后回到开盘价下方，说明开盘承接不足，优先观察 VWAP 能否收复。"
    if trend_label == "低开修复":
        return "若修复至 VWAP 上方并接近开盘高点，可观察反弹质量和指数配合。"
    if vwap_position == "above" and range_position in {"near_high", "breakout_up"}:
        return "价格靠近开盘区间上沿，观察是否放量突破，而不是冲高回落。"
    if vwap_position == "below" and range_position in {"near_low", "breakdown_down"}:
        return "价格靠近开盘区间下沿，观察 VWAP 下方停留时间和低点是否被击穿。"
    return "价格位于开盘区间中部，先观察 VWAP 方向和指数强弱，不急于追随单根波动。"
