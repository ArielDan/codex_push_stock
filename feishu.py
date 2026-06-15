"""Feishu custom bot webhook sender."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import json
import os
import re
import time
from typing import Optional

import requests


FEISHU_RATE_LIMIT_CODE = 11232
FEISHU_RETRY_DELAYS = (0, 30, 60, 120)


def build_card_payload(report: str, quotes=None, report_date: Optional[date] = None) -> dict:
    if quotes and report_date:
        return _build_native_table_payload(report, quotes, report_date)

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


def _build_native_table_payload(report: str, quotes, report_date: date) -> dict:
    grouped = defaultdict(list)
    for quote in quotes:
        grouped[quote.group_key].append(quote)

    card = {
        "schema": "2.0",
        "header": {
            "template": _header_template(grouped),
            "title": {
                "tag": "plain_text",
                "content": f"美股收盘简报｜{report_date.isoformat()}",
            },
        },
        "body": {
            "elements": _build_native_elements(report, grouped),
        },
    }
    return {"msg_type": "interactive", "card": card}


def _build_native_elements(report: str, grouped) -> list[dict]:
    sections = _split_sections(_split_title(report)[1])
    section_map = {_section_title(section): section for section in sections}

    elements = []
    elements.append(_markdown_div("**一、核心指数 / ETF**"))
    elements.append(_quote_table("core_table", grouped["core"], include_price=True, page_size=10))
    elements.append({"tag": "hr"})

    macro = section_map.get("二、宏观 / 风险")
    if macro:
        elements.append(_markdown_div(macro))
        elements.append({"tag": "hr"})

    elements.append(_markdown_div("**三、板块观察**"))
    elements.append(_sector_table(grouped))
    elements.append({"tag": "hr"})

    for title in ("四、一句话判断", "五、下一交易日观察重点"):
        section = section_map.get(title)
        if section:
            elements.append(_markdown_div(section))
            if title != "五、下一交易日观察重点":
                elements.append({"tag": "hr"})
    return elements


def _markdown_div(content: str) -> dict:
    return {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": content,
        },
    }


def _quote_table(element_id: str, quotes, include_price: bool, page_size: int) -> dict:
    columns = [
        {"name": "ticker", "display_name": "标的", "data_type": "text", "width": "80px"},
    ]
    if include_price:
        columns.append(
            {
                "name": "close",
                "display_name": "收盘",
                "data_type": "number",
                "width": "90px",
                "format": {"precision": 2, "separator": False},
            }
        )
    columns.append({"name": "change", "display_name": "涨跌", "data_type": "options", "width": "90px"})

    rows = []
    for quote in quotes:
        row = {
            "ticker": quote.ticker,
            "change": [_change_option(quote.pct_change)],
        }
        if include_price:
            row["close"] = _display_value(quote) if quote.close is not None else None
        rows.append(row)

    return {
        "tag": "table",
        "element_id": element_id,
        "page_size": min(max(page_size, 1), 10),
        "row_height": "low",
        "freeze_first_column": True,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "grey",
            "text_color": "grey",
            "bold": True,
            "lines": 1,
        },
        "columns": columns,
        "rows": rows,
    }


def _core_compact_table(quotes) -> dict:
    rows = []
    for index in range(0, len(quotes), 2):
        left = quotes[index]
        right = quotes[index + 1] if index + 1 < len(quotes) else None
        row = {
            "leftticker": left.ticker,
            "leftchange": _change_text(left.pct_change),
            "rightticker": right.ticker if right else "",
            "rightchange": _change_text(right.pct_change) if right else "",
        }
        rows.append(row)

    return {
        "tag": "table",
        "element_id": "core_table",
        "page_size": 10,
        "row_height": "low",
        "freeze_first_column": False,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "grey",
            "text_color": "grey",
            "bold": True,
            "lines": 1,
        },
        "columns": [
            {"name": "leftticker", "display_name": "标的A", "data_type": "text", "width": "70px"},
            {"name": "leftchange", "display_name": "涨跌A", "data_type": "text", "width": "85px"},
            {"name": "rightticker", "display_name": "标的B", "data_type": "text", "width": "70px"},
            {"name": "rightchange", "display_name": "涨跌B", "data_type": "text", "width": "85px"},
        ],
        "rows": rows,
    }


def _sector_table(grouped) -> dict:
    table_groups = [
        ("ai_semis", "AI/半导体", "semi"),
        ("ai_power", "AI电力", "power"),
        ("commodities", "贵金属/大宗", "commodity"),
    ]
    max_rows = max((len(grouped[key]) for key, _, _ in table_groups), default=0)
    rows = []
    for index in range(max_rows):
        row = {}
        for key, _, prefix in table_groups:
            quote = grouped[key][index] if index < len(grouped[key]) else None
            row[f"{prefix}ticker"] = quote.ticker if quote else ""
            row[f"{prefix}change"] = _change_text(quote.pct_change) if quote else ""
        rows.append(row)

    return {
        "tag": "table",
        "element_id": "sector_table",
        "page_size": 10,
        "row_height": "low",
        "freeze_first_column": True,
        "header_style": {
            "text_align": "left",
            "text_size": "normal",
            "background_style": "grey",
            "text_color": "grey",
            "bold": True,
            "lines": 1,
        },
        "columns": [
            {"name": "semiticker", "display_name": "AI/半导体", "data_type": "text", "width": "90px"},
            {"name": "semichange", "display_name": "半导体涨跌", "data_type": "text", "width": "90px"},
            {"name": "powerticker", "display_name": "AI电力", "data_type": "text", "width": "90px"},
            {"name": "powerchange", "display_name": "电力涨跌", "data_type": "text", "width": "90px"},
            {"name": "commodityticker", "display_name": "贵金属/大宗", "data_type": "text", "width": "110px"},
            {"name": "commoditychange", "display_name": "大宗涨跌", "data_type": "text", "width": "90px"},
        ],
        "rows": rows,
    }


def _change_option(value: Optional[float]) -> dict:
    if value is None:
        return {"text": "缺失", "color": "blue"}
    text = f"{value:+.2f}%"
    if value > 0:
        return {"text": text, "color": "green"}
    if value < 0:
        return {"text": text, "color": "red"}
    return {"text": text, "color": "blue"}


def _change_text(value: Optional[float]) -> str:
    if value is None:
        return "缺失"
    prefix = "🟢" if value > 0 else "🔴" if value < 0 else "⚪️"
    return f"{prefix} {value:+.2f}%"


def _blank_option() -> dict:
    return {"text": "-", "color": "blue"}


def _display_value(quote) -> float:
    if quote.ticker == "^TNX" and quote.close is not None:
        return quote.close / 10 if quote.close > 20 else quote.close
    return (quote.close or 0) / quote.display_divisor


def _format_close(quote) -> str:
    if not quote or quote.close is None:
        return ""
    return f"{_display_value(quote):.2f}{quote.display_suffix}"


def _header_template(grouped) -> str:
    qqq = _find_quote(grouped["core"], "QQQ")
    voo = _find_quote(grouped["core"], "VOO")
    if qqq and voo and qqq.pct_change is not None and voo.pct_change is not None:
        if qqq.pct_change > 0 and voo.pct_change > 0:
            return "green"
        if qqq.pct_change < 0 and voo.pct_change < 0:
            return "red"
    return "blue"


def _find_quote(quotes, ticker: str):
    for quote in quotes:
        if quote.ticker == ticker:
            return quote
    return None


def _section_title(section: str) -> str:
    first_line = section.splitlines()[0].strip()
    return first_line.strip("*")


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


def send_report(report: str, webhook: Optional[str] = None, quotes=None, report_date: Optional[date] = None) -> None:
    target = webhook or os.getenv("FEISHU_WEBHOOK")
    if not target:
        raise RuntimeError("FEISHU_WEBHOOK 未配置；如需本地预览请使用 python main.py --dry-run 或 python3 main.py --dry-run")

    body = json.dumps(build_card_payload(report, quotes=quotes, report_date=report_date), ensure_ascii=False).encode("utf-8")
    last_error = None
    for attempt, delay in enumerate(FEISHU_RETRY_DELAYS, start=1):
        if delay:
            print(f"WARNING: 飞书限频，等待 {delay} 秒后重试（{attempt}/{len(FEISHU_RETRY_DELAYS)}）")
            time.sleep(delay)

        response = requests.post(
            target,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=20,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"飞书发送失败：HTTP {response.status_code} {response.text}")

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        status_code = payload.get("StatusCode", 0)
        code = payload.get("code", 0)
        if status_code in (0, None) and code in (0, None):
            return

        last_error = f"飞书发送失败：HTTP {response.status_code} {response.text}"
        if code != FEISHU_RATE_LIMIT_CODE and "frequency limited" not in response.text:
            raise RuntimeError(last_error)

    print("WARNING: 飞书卡片限频重试后仍未成功，尝试发送普通文本兜底消息")
    fallback_error = _send_plain_text_fallback(target, report)
    if fallback_error:
        raise RuntimeError(f"{last_error or '飞书卡片发送失败'}；普通文本兜底也失败：{fallback_error}")


def _send_plain_text_fallback(target: str, report: str) -> Optional[str]:
    text = "【美股收盘简报】\n飞书卡片发送被限频，以下为文本兜底版：\n\n" + report
    body = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode("utf-8")
    response = requests.post(
        target,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=20,
    )
    if response.status_code >= 400:
        return f"HTTP {response.status_code} {response.text}"

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    status_code = payload.get("StatusCode", 0)
    code = payload.get("code", 0)
    if status_code in (0, None) and code in (0, None):
        return None
    return f"HTTP {response.status_code} {response.text}"
