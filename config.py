"""Runtime defaults and watchlist loading for the daily market report."""

from __future__ import annotations

import json
from pathlib import Path

LOOKBACK_DAYS = 7
BEIJING_TIMEZONE = "Asia/Shanghai"
WATCHLIST_PATH = Path(__file__).resolve().parent / "watchlist.json"


def load_asset_groups() -> list[dict]:
    with WATCHLIST_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def all_assets() -> list[dict]:
    assets = []
    for group in load_asset_groups():
        for asset in group["assets"]:
            merged = dict(asset)
            merged["group_key"] = group["key"]
            merged["group_title"] = group["title"]
            assets.append(merged)
    return assets
