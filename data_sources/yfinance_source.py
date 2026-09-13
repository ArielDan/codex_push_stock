"""yfinance based end-of-day data source."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from pathlib import Path

from .base import DailyBar

logger = logging.getLogger(__name__)


class YFinanceSource:
    name = "yfinance"

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError("缺少 yfinance 依赖，请先安装 requirements.txt") from exc

        try:
            cache_dir = Path(".yfinance_cache").resolve()
            cache_dir.mkdir(exist_ok=True)
            yf.set_tz_cache_location(str(cache_dir))
        except Exception:
            logger.debug("无法设置 yfinance 本地缓存目录", exc_info=True)

        # Ask for more calendar days than needed so weekends and holidays still leave
        # enough completed trading sessions for percent-change calculations.
        start = (date.today() - timedelta(days=lookback_days + 10)).isoformat()
        end = (date.today() + timedelta(days=1)).isoformat()

        try:
            history = yf.Ticker(ticker).history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                actions=False,
            )
        except Exception as exc:
            raise RuntimeError(f"yfinance 拉取 {ticker} 失败：{exc}") from exc

        bars: list[DailyBar] = []
        for index, row in history.tail(lookback_days + 2).iterrows():
            close = row.get("Close")
            if close is None or close != close:
                continue

            raw_date = index.date() if hasattr(index, "date") else index
            if isinstance(raw_date, datetime):
                raw_date = raw_date.date()
            bars.append(DailyBar(date=raw_date, close=float(close)))

        if not bars:
            logger.warning("%s 未返回有效 yfinance 日线数据", ticker)
        return bars
