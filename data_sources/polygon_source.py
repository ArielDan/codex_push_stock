"""Polygon/Massive compatible end-of-day data source."""

from __future__ import annotations

from datetime import date, timedelta
import os
from typing import Optional

import requests

from .base import DailyBar


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
