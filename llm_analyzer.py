"""Optional LLM-powered market view generation."""

from __future__ import annotations

import json
import os
from typing import Optional, TypedDict

import requests


class LLMAnalysis(TypedDict):
    label: str
    market_view: str
    watch_points: list[str]


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
                    "你的任务是基于用户提供的行情数据、watchlist 分组、已确认事件、"
                    "可验证外部信息和你的市场分析能力，判断美股收盘后的市场状态，"
                    "补充当天最重要的市场信息，并给出下一交易日观察重点和可执行投资建议。"
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
                    "9. 输出中文，适合飞书手机端阅读，简洁、具体、克制。"
                    "分析框架：请根据当天数据和事件，自主选择最重要的分析角度。"
                    "可参考但不限于：市场状态、主线变化、宏观环境、板块联动、异常信号、"
                    "持仓影响、交易含义。"
                    "输出要求：必须返回 JSON。可以在 JSON 字段中补充必要解释，但不要脱离 JSON 格式。"
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(quotes),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1400,
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
    lines = [
        "请参考以下收盘数据生成「每日美股收盘简报」的模型判断、信息补充和投资建议。",
        "要求：",
        "- 可以结合可验证外部信息补充当天最重要的市场事件。",
        "- 补充信息必须区分 confirmed / uncertain / needs_verification。",
        "- 不编造新闻归因；无法确认驱动时写「未确认具体驱动」。",
        "- 事实数据和模型判断必须分离。",
        "- 投资建议必须包含：结论、依据、风险、可执行动作、信心分 1-10。",
        "- market_view 输出一段分析总结，不超过500个中文字符。",
        "- watch_points 输出1-5条，每条不超过 200个中文字符。",
        "- confidence 必须是 1-10 的整数。",
        "- 必须返回 JSON。",
        "- JSON 格式：",
        (
            '{"facts":["关键事实1","关键事实2"],'
            '"supplemental_info":[{"event":"补充事件","relevance":"相关性",'
            '"certainty":"confirmed / uncertain / needs_verification"}],'
            '"market_view":"模型判断",'
            '"watch_points":["观察重点1","观察重点2"],'
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
        return {
            "label": label,
            "market_view": _clean_model_text(content),
            "watch_points": [],
        }

    market_view = _clean_model_text(str(payload.get("market_view", "")).strip())
    watch_points = payload.get("watch_points") or []
    cleaned_points = []
    for point in watch_points:
        text = str(point).strip()
        if text:
            cleaned_points.append(text.lstrip("- ").strip())
    return {
        "label": label,
        "market_view": market_view,
        "watch_points": cleaned_points[:5],
    }


def _extract_json_text(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

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
