"""Optional LLM-powered market view generation."""

from __future__ import annotations

import json
import os
import re
from calendar import monthrange
from datetime import date
from typing import Optional, TypedDict

import requests


class LLMAnalysis(TypedDict, total=False):
    label: str
    market_view: str
    key_observations: list[str]
    watch_points: list[str]
    investment_advice: str


def generate_market_analysis(quotes) -> Optional[LLMAnalysis]:
    api_key = (os.getenv("LLM_API_KEY") or "").strip()
    base_url = (os.getenv("LLM_BASE_URL") or "").strip()
    model = (os.getenv("LLM_MODEL") or "").strip()
    if not api_key or not base_url or not model:
        return None

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是我的个人投资分析员，负责生成「每日美股收盘简报」中的模型判断、"
                    "信息补充和投资建议。"
                    "你的任务不是复述涨跌流水账，而是从用户重点观察标的、行情结构、"
                    "宏观环境、资金面/仓位线索、关键日历和可验证外部信息中，提炼对下一步交易"
                    "真正有用的 3-5 个观察。"
                    "硬性规则："
                    "1. 必须严格区分「事实数据」和「模型判断」。"
                    "2. 用户提供的行情、涨跌幅、分组、收盘价属于事实数据；"
                    "你对趋势、风险偏好、板块强弱、交易含义的解释属于模型判断。"
                    "3. 可以补充可验证的外部信息，例如重大宏观数据、公司财报、监管变化、"
                    "行业新闻、资金流或盘中重大事件。"
                    "4. 补充信息必须是你有把握的事实；不确定的信息必须标注「待验证」或"
                    "「不确定」，不能写成确定事实。"
                    "5. 不得编造新闻、政策、财报、官员讲话、管理层表态、盘中事件或市场传闻。"
                    "6. 如果没有可靠信息确认某个驱动原因，必须写「未确认具体驱动」，"
                    "不能强行归因。"
                    "7. 投资建议必须包含：结论、依据、风险、可执行动作、信心分 1-10。"
                    "8. 重点关注但不限于：美股大盘、VIX、10Y 美债收益率、美元、AI/半导体、"
                    "AI 电力、贵金属/大宗、加密相关股票，以及这些信号对港股和 A 股基金/ETF 的影响。"
                    "9. 增加宏观和资金面观察：风险偏好、利率/美元/流动性、信用或避险信号、"
                    "期权波动率、CTA/系统性资金可能的仓位压力、机构月末/季末再平衡、"
                    "CNN Fear & Greed、BofA Bull & Bear 等情绪/资金指标。"
                    "10. 这些外部指标如果没有可靠当前数值，不要编数值；可以写成「待验证观察」或"
                    "「需确认的资金面线索」。"
                    "11. 输出中文，适合飞书手机端阅读，简洁、具体、克制。"
                    "分析框架：请根据当天数据和事件，自主选择最重要的分析角度。"
                    "可参考但不限于：市场状态、主线变化、宏观/资金环境、板块联动、异常信号、"
                    "关键日历、持仓影响、交易含义。"
                    "输出要求：必须返回 JSON。可以在 JSON 字段中补充必要解释，但不要脱离 JSON 格式。"
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(quotes),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(
        _chat_completions_url(base_url),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=float(os.getenv("LLM_TIMEOUT", "30")),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"模型 API 调用失败：HTTP {response.status_code} {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    return _parse_analysis(content, _display_model_name(model))


def generate_market_view(quotes) -> Optional[str]:
    analysis = generate_market_analysis(quotes)
    if not analysis:
        return None
    return f"{analysis['label']}：{analysis['market_view']}"


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def _build_prompt(quotes) -> str:
    report_date = _report_date_from_quotes(quotes)
    calendar_context = _calendar_context(report_date)
    lines = [
        "请参考以下收盘数据生成「每日美股收盘简报」的模型判断、资金面观察和投资建议。",
        f"报告日期：{report_date.isoformat() if report_date else '未知'}",
        f"日历背景：{calendar_context}",
        "要求：",
        "- 不要流水账罗列涨跌；优先回答：这组信号对下一步仓位/观察/交易意味着什么。",
        "- 必须覆盖：大盘结构、风险偏好、利率/美元、半导体和 AI 电力强弱、贵金属/大宗。",
        "- 尽量增加宏观和资金面视角：Fear & Greed、BofA Bull & Bear、CTA 标准线/趋势仓位、期权/VIX、月末/季末再平衡、FOMC/CPI/PCE/NFP/期权到期等关键时间点。",
        "- 如果你没有这些外部指标的可靠最新数值，不要编数值；可以写成待验证线索或观察重点。",
        "- 可以结合可验证外部信息补充当天最重要的市场事件，最多 2 件，并直接融入 market_view 或 watch_points。",
        "- 外部事件不确定时必须写「待验证」，不要单独展开长篇事实列表。",
        "- 不编造新闻归因；无法确认驱动时写「未确认具体驱动」。",
        "- 事实数据和模型判断必须分离。",
        "- 投资建议必须具体，包含：结论、依据、风险、可执行动作、信心分 1-10。",
        "- market_view 输出一段分析总结，建议 500-900 个中文字符，必须包含宏观/资金面含义。",
        "- key_observations 输出3-5条，每条不超过 220个中文字符，用于保留重要投资观察：宏观/资金面、板块结构、待验证事件、跨市场联动、仓位含义。",
        "- watch_points 输出3-5条，每条不超过 220个中文字符，至少 1 条是宏观/资金面或关键日历观察。",
        "- confidence 必须是 1-10 的整数。",
        "- 必须返回 JSON，不要 Markdown，不要代码块，不要 ```json。",
        "- JSON 格式：",
        (
            '{"market_view":"模型判断",'
            '"key_observations":["关键观察1","关键观察2","关键观察3"],'
            '"watch_points":["下一交易日观察重点1","下一交易日观察重点2","下一交易日观察重点3"],'
            '"investment_advice":{"conclusion":"结论","basis":"依据","risks":"风险",'
            '"action":"可执行动作","confidence":1}}'
        ),
        "",
        "行情数据：",
    ]
    for quote in quotes:
        if quote.close is None or quote.pct_change is None:
            continue
        close = _display_value(quote)
        suffix = quote.display_suffix
        lines.append(
            f"- {quote.group_title}｜{quote.ticker}：收盘 {close:.2f}{suffix}，涨跌 {quote.pct_change:+.2f}%"
        )
    return "\n".join(lines)


def _report_date_from_quotes(quotes) -> Optional[date]:
    dates = [quote.date for quote in quotes if quote.date]
    return max(dates) if dates else None


def _calendar_context(report_date: Optional[date]) -> str:
    if not report_date:
        return "未获取到报告日期。"

    _, last_day = monthrange(report_date.year, report_date.month)
    days_to_month_end = last_day - report_date.day
    context = []
    if days_to_month_end <= 5:
        context.append("接近月末，留意机构基金月末再平衡、CTA/风险平价调仓和期权仓位影响")
    if report_date.month in {3, 6, 9, 12} and days_to_month_end <= 7:
        context.append("接近季度末，留意养老金/共同基金再平衡、窗口粉饰和流动性变化")
    if report_date.day <= 5:
        context.append("月初阶段，留意新资金配置、非农就业数据窗口和月度宏观数据重定价")
    context.append("若临近 FOMC、CPI、PCE、NFP、OPEX 或重大财报窗口，需要在观察重点中提示")
    return "；".join(context)


def _display_value(quote) -> float:
    if quote.ticker == "^TNX" and quote.close is not None:
        return quote.close / 10 if quote.close > 20 else quote.close
    return (quote.close or 0) / quote.display_divisor


def _single_line(text: str) -> str:
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def _clean_model_text(text: str) -> str:
    cleaned = _single_line(text)
    for prefix in ("模型判断：", "模型判断:", "判断：", "判断:"):
        if cleaned.startswith(prefix):
            return cleaned[len(prefix) :].strip()
    return cleaned


def _parse_analysis(content: str, label: str) -> LLMAnalysis:
    json_text = _extract_json_text(content)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError:
        recovered = _recover_partial_analysis(content, label)
        if recovered:
            return recovered
        return {
            "label": "非模型结果",
            "market_view": "",
            "watch_points": [],
        }

    market_view = _clean_model_text(str(payload.get("market_view", "")).strip())
    advice = _format_investment_advice(payload.get("investment_advice"))
    key_observations = _clean_text_items(payload.get("key_observations") or payload.get("supplemental_info") or [])
    watch_points = payload.get("watch_points") or []
    return {
        "label": label,
        "market_view": market_view,
        "key_observations": key_observations[:5],
        "watch_points": _clean_text_items(watch_points)[:5],
        "investment_advice": advice,
    }


def _recover_partial_analysis(content: str, label: str) -> Optional[LLMAnalysis]:
    text = _extract_json_text(content)
    market_view = _extract_json_string_field(text, "market_view")
    key_observations = _extract_json_string_array(text, "key_observations")
    if not key_observations:
        key_observations = _recover_supplemental_info(text)
    watch_points = _extract_json_string_array(text, "watch_points")
    advice = _recover_investment_advice(text)
    if not market_view and not key_observations and not watch_points:
        return None
    return {
        "label": label,
        "market_view": _clean_model_text(market_view),
        "key_observations": key_observations[:5],
        "watch_points": watch_points[:5],
        "investment_advice": advice,
    }


def _clean_text_items(items) -> list[str]:
    cleaned = []
    for item in items:
        if isinstance(item, dict):
            parts = [
                str(item.get("event", "")).strip(),
                str(item.get("relevance", "")).strip(),
                str(item.get("certainty", "")).strip(),
            ]
            text = "；".join(part for part in parts if part)
        else:
            text = str(item).strip()
        if text:
            cleaned.append(text.lstrip("- ").strip())
    return cleaned


def _extract_json_string_field(text: str, field: str) -> str:
    pattern = rf'"{re.escape(field)}"\s*:\s*"((?:\\.|[^"\\])*)'
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return ""
    return _decode_json_string_fragment(match.group(1))


def _extract_json_string_array(text: str, field: str) -> list[str]:
    match = re.search(rf'"{re.escape(field)}"\s*:\s*\[(.*?)\]', text, flags=re.DOTALL)
    if not match:
        return []
    items = re.findall(r'"((?:\\.|[^"\\])*)"', match.group(1), flags=re.DOTALL)
    return [_decode_json_string_fragment(item).lstrip("- ").strip() for item in items if item.strip()]


def _recover_supplemental_info(text: str) -> list[str]:
    match = re.search(r'"supplemental_info"\s*:\s*\[(.*?)\]\s*,\s*"market_view"', text, flags=re.DOTALL)
    if not match:
        return []

    observations = []
    for chunk in re.findall(r"\{(.*?)\}", match.group(1), flags=re.DOTALL):
        event = _extract_json_string_field("{" + chunk + "}", "event")
        relevance = _extract_json_string_field("{" + chunk + "}", "relevance")
        certainty = _extract_json_string_field("{" + chunk + "}", "certainty")
        parts = [part for part in (event, relevance, certainty) if part]
        if parts:
            observations.append("；".join(parts))
    return observations


def _recover_investment_advice(text: str) -> str:
    advice = {
        "conclusion": _extract_json_string_field(text, "conclusion"),
        "action": _extract_json_string_field(text, "action"),
        "risks": _extract_json_string_field(text, "risks"),
    }
    confidence_match = re.search(r'"confidence"\s*:\s*("?)(\d+)\1', text)
    if confidence_match:
        advice["confidence"] = confidence_match.group(2)
    return _format_investment_advice(advice)


def _decode_json_string_fragment(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace('\\"', '"').replace("\\n", " ")


def _format_investment_advice(advice) -> str:
    if not isinstance(advice, dict):
        return ""

    parts = []
    conclusion = _single_line(str(advice.get("conclusion", "")).strip())
    action = _single_line(str(advice.get("action", "")).strip())
    risks = _single_line(str(advice.get("risks", "")).strip())
    confidence = advice.get("confidence")
    if conclusion:
        parts.append(f"结论：{conclusion}")
    if action:
        parts.append(f"动作：{action}")
    if risks:
        parts.append(f"风险：{risks}")
    if confidence not in (None, ""):
        parts.append(f"信心：{confidence}/10")
    return "；".join(parts)


def _extract_json_text(content: str) -> str:
    text = content.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)(?:```)?\s*$", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    if text.lower().startswith("json"):
        text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _display_model_name(model: str) -> str:
    aliases = {
        "anthropic": "Claude",
        "openai": "OpenAI",
        "google": "Gemini",
        "meta-llama": "Llama",
        "deepseek": "DeepSeek",
        "qwen": "Qwen",
        "mistralai": "Mistral",
    }
    provider = model.split("/", 1)[0].strip()
    return aliases.get(provider, provider or model)
