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
                    "你是一个资深的证券交易分析员，现在要做美股收盘简报分析助手。"
                    "用户提供的是当前重点观察标的和行情数据，不是唯一信息源。"
                    "你可以结合可验证的外部信息源补充分析；盘中如果有重大事件发生，挑选最重大的3件来输出。"
                    "不要编造新闻、政策、财报、官员讲话或盘中事件；无法确认的信息不要写。"
                    "最后给出下你的下一步投资建议，并附上你的判断信息值，满分是10分。"
                    "输出中文，适合飞书手机端阅读。必须只返回 JSON，不要输出 Markdown。"
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(quotes),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
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
        "请参考以下收盘数据生成「模型判断」。",
        "要求：",
        "- 关注大盘、风险偏好、波动率、利率、美元、半导体产业、AI电力、贵金属/大宗的强弱。",
        "- market_view 输出一段分析总结，不超过500个中文字符。",
        "- watch_points 输出1-5条，每条不超过 200个中文字符。",
        "- 只返回 JSON：{\"market_view\":\"...\",\"watch_points\":[\"...\",\"...\",\"...\"]}",
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
    try:
        payload = json.loads(content)
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
