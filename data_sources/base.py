"""Shared market data source contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class DailyBar:
    date: date
    close: float


class MarketDataSource(Protocol):
    name: str

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        """Return daily close bars sorted from oldest to newest."""

