"""Feishu custom bot webhook sender."""

from __future__ import annotations

import json
import os
import re
from typing import Optional

import requests


def build_card_payload(report: str) -> dict:
    title, content = _split_title(report)
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": title,
                },
            },
            "elements": _build_card_elements(content),
        },
    }


def _split_title(report: str) -> tuple[str, str]:
    lines = report.splitlines()
    if not lines:
        return "美股收盘简报", ""

    raw_title = lines[0].strip()
    title = raw_title.strip("【】") or "美股收盘简报"
    content_lines = lines[1:]
    while content_lines and not content_lines[0].strip():
        content_lines.pop(0)
    return title, "\n".join(content_lines)


def _build_card_elements(content: str) -> list[dict]:
    sections = _split_sections(content)
    elements = []
    for index, section in enumerate(sections):
        elements.append({"tag": "markdown", "content": section})
        if index < len(sections) - 1:
            elements.append({"tag": "hr"})
    return elements


def _split_sections(content: str) -> list[str]:
    chunks = re.split(r"\n(?=\*\*[一二三四五六七八九十]、)", content.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


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
