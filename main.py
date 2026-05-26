"""Daily US market close report entrypoint."""

from __future__ import annotations

import argparse
from datetime import date
import logging
import os
from pathlib import Path
import sys
from typing import Optional

from config import LOOKBACK_DAYS, all_assets
from data_sources import PolygonSource, YFinanceSource
from feishu import send_report
from report_builder import build_report, quote_from_bars


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(__file__).resolve().parent / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每日美股收盘简报飞书推送")
    parser.add_argument("--dry-run", action="store_true", help="只打印报告，不发送飞书")
    return parser.parse_args()


def build_sources():
    fallback = YFinanceSource()
    if os.getenv("POLYGON_API_KEY"):
        try:
            return [PolygonSource(), fallback]
        except Exception as exc:
            logger.warning("Polygon 初始化失败，将使用 yfinance：%s", exc)
    return [fallback]


def fetch_quotes():
    sources = build_sources()
    quotes = []
    for asset in all_assets():
        last_error = None
        for source in sources:
            try:
                bars = source.get_daily_bars(asset["ticker"], LOOKBACK_DAYS)
                if bars:
                    quotes.append(quote_from_bars(asset, bars, source.name))
                    break
                last_error = RuntimeError(f"{source.name} 无有效数据")
            except Exception as exc:
                last_error = exc
                logger.warning("%s 使用 %s 拉取失败：%s", asset["ticker"], source.name, exc)
        else:
            logger.warning("%s 数据缺失：%s", asset["ticker"], last_error)
            quotes.append(quote_from_bars(asset, [], sources[-1].name))
    return quotes


def find_report_date(quotes) -> Optional[date]:
    core_dates = [
        quote.date
        for quote in quotes
        if quote.group_key == "core" and quote.ticker in {"QQQ", "VOO", "DIA", "IWM"} and quote.date
    ]
    if not core_dates:
        return None
    return max(core_dates)


def main() -> int:
    args = parse_args()
    load_dotenv_if_available()

    quotes = fetch_quotes()
    report_date = find_report_date(quotes)
    report = build_report(quotes, report_date)

    if args.dry_run:
        print(report)
        return 0

    try:
        send_report(report, quotes=quotes, report_date=report_date)
    except Exception as exc:
        logger.error("%s", exc)
        return 1

    logger.info("飞书推送完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
