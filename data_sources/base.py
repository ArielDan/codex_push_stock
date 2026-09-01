"""Shared market data source contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class DailyBar:
    date: date
    close: float


@dataclass(frozen=True)
class IntradayBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class MarketDataSource(Protocol):
    name: str

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        """Return daily close bars sorted from oldest to newest."""
