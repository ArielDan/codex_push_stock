"""Polygon/Massive compatible end-of-day data source."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import os
from typing import Optional
from zoneinfo import ZoneInfo

import requests

from .base import DailyBar, IntradayBar


class PolygonSource:
    name = "polygon"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY 未配置")

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        if ticker.startswith("^") or "." in ticker:
            raise RuntimeError(f"{ticker} 不是 Polygon MVP 默认支持的股票 ticker")

        end = date.today()
        start = end - timedelta(days=lookback_days + 10)
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
            f"{start.isoformat()}/{end.isoformat()}"
        )
        response = requests.get(
            url,
            params={
                "adjusted": "true",
                "sort": "asc",
                "limit": lookback_days + 10,
                "apiKey": self.api_key,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Polygon 拉取 {ticker} 失败：{response.status_code} {response.text}")

        payload = response.json()
        results = payload.get("results") or []
        bars = []
        for item in results[-(lookback_days + 2) :]:
            close = item.get("c")
            timestamp = item.get("t")
            if close is None or timestamp is None:
                continue
            bars.append(DailyBar(date=date.fromtimestamp(timestamp / 1000), close=float(close)))
        return bars

    def get_intraday_bars(self, ticker: str, session_date: date, interval: str = "1m") -> list[IntradayBar]:
        if ticker.startswith("^") or "." in ticker:
            raise RuntimeError(f"{ticker} 不是 Polygon MVP 默认支持的股票 ticker")

        multiplier = 5 if interval == "5m" else 1
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/minute/"
            f"{session_date.isoformat()}/{session_date.isoformat()}"
        )
        response = requests.get(
            url,
            params={
                "adjusted": "true",
                "sort": "asc",
                "limit": 5000,
                "apiKey": self.api_key,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Polygon 拉取 {ticker} 盘中数据失败：{response.status_code} {response.text}")

        ny_tz = ZoneInfo("America/New_York")
        bars: list[IntradayBar] = []
        for item in response.json().get("results") or []:
            timestamp_ms = item.get("t")
            if timestamp_ms is None:
                continue
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).astimezone(ny_tz)
            if timestamp.date() != session_date:
                continue
            try:
                bars.append(
                    IntradayBar(
                        timestamp=timestamp,
                        open=float(item["o"]),
                        high=float(item["h"]),
                        low=float(item["l"]),
                        close=float(item["c"]),
                        volume=float(item.get("v") or 0),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return bars
