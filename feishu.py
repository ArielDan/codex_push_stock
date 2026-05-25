"""Feishu custom bot webhook sender."""

from __future__ import annotations

import json
import os
from typing import Optional

import requests


def build_card_payload(report: str) -> dict:
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": report,
                }
            ],
        },
    }


def send_report(report: str, webhook: Optional[str] = None) -> None:
    target = webhook or os.getenv("FEISHU_WEBHOOK")
    if not target:
        raise RuntimeError("FEISHU_WEBHOOK 未配置；如需本地预览请使用 python main.py --dry-run 或 python3 main.py --dry-run")

    response = requests.post(
        target,
        data=json.dumps(build_card_payload(report), ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"飞书发送失败：HTTP {response.status_code} {response.text}")

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if payload.get("StatusCode", 0) not in (0, None) or payload.get("code", 0) not in (0, None):
        raise RuntimeError(f"飞书发送失败：HTTP {response.status_code} {response.text}")
