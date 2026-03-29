"""
Direct HTTP clients for sponsor APIs used by registry agents:

- pipeline_classifier / gemini_api → Gemini generateContent, with ``gemini_or_light_*`` fallbacks
- image_multimodal_processor / gemini_vision → same Gemini model (multimodal-capable)
- elevenlabs_narration → ElevenLabs text-to-speech
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
# Default voice (Rachel) — override via ELEVENLABS_VOICE_ID in env if we add it later
DEFAULT_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


def normalize_openai_compat_model_slug(model: str) -> str:
    """
    Normalize model id for OpenAI-compatible chat/completions HTTP calls.

    Featherless expects the catalog model ``id`` exactly as returned by ``GET /v1/models``
    (e.g. ``deepseek-ai/DeepSeek-V3.2``). A LiteLLM-style ``openai/org/model`` prefix
    produces ``model_not_found`` (404) on Featherless.
    """
    normalized = (model or "").strip()
    if not normalized:
        return normalized
    base = (settings.llm_base_url or "").lower()
    if "featherless.ai" in base:
        return normalized
    if "/" in normalized and not normalized.startswith(("openai/", "azure/", "gemini/")):
        return f"openai/{normalized}"
    return normalized


def llm_chat_completion(
    model: str,
    user_message: str,
    system_instruction: str | None = None,
    max_tokens: int = 800,
) -> str:
    """Send a chat completion via Featherless (OpenAI-compatible API)."""
    if not settings.llm_api_key_configured:
        raise ValueError("LLM_API_KEY is not set in apps/api/.env")

    model = normalize_openai_compat_model_slug(model)

    base = settings.llm_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    messages: list[dict[str, str]] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": user_message})

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key.strip()}",
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"LLM API error {resp.status_code}: {resp.text[:2000]}",
            )
        data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM API returned no choices: {json.dumps(data)[:1500]}")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    return content or "(empty model response)"


def llm_chat_with_messages(
    messages: list[tuple[str, str]],
    system_instruction: str | None = None,
    *,
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    """
    Multi-turn chat via OpenAI-compatible API (Featherless).

    Each tuple is (role, text) where role is \"user\" or \"model\" (assistant).
    Default model is ``heavy_alt_model`` (falls back to ``heavy_model``).
    """
    if not settings.llm_api_key_configured:
        raise ValueError("LLM_API_KEY is not set in apps/api/.env")

    resolved = (model or settings.heavy_alt_model or settings.heavy_model or "").strip()
    if not resolved:
        raise ValueError("No heavy_alt_model / heavy_model configured")

    resolved = normalize_openai_compat_model_slug(resolved)

    oa_messages: list[dict[str, str]] = []
    if system_instruction:
        oa_messages.append({"role": "system", "content": system_instruction})
    for role, text in messages:
        r = (role or "").strip().lower()
        oa_role = "assistant" if r in ("assistant", "model") else "user"
        oa_messages.append({"role": oa_role, "content": text})

    base = settings.llm_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    body = {
        "model": resolved,
        "messages": oa_messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key.strip()}",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"LLM API error {resp.status_code}: {resp.text[:2000]}",
            )
        data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM API returned no choices: {json.dumps(data)[:1500]}")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    return content or "(empty model response)"


openai_compat_chat_completion = llm_chat_completion


def gemini_chat_completion(user_message: str, system_instruction: str | None = None) -> str:
    if not settings.gemini_api_key_configured:
        raise ValueError("GEMINI_API_KEY is not set in apps/api/.env")

    model = (settings.gemini_model or "gemini-2.5-flash").strip()
    url = GEMINI_GENERATE_URL.format(model=model)
    params = {"key": settings.gemini_api_key.strip()}

    body: dict = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, params=params, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Gemini API error {resp.status_code}: {resp.text[:2000]}",
            )
        data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:1500]}")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
    return "".join(texts).strip() or "(empty model response)"


def gemini_or_light_chat_completion_pair(
    user_message: str,
    system_instruction: str | None = None,
    *,
    max_tokens: int = 800,
) -> tuple[str, str]:
    """
    Prefer Gemini when configured; on failure (or missing key), use ``LIGHT_MODEL`` via Featherless.

    Returns ``(text, "gemini" | "light_model")``.
    """
    if settings.gemini_api_key_configured:
        try:
            return gemini_chat_completion(user_message, system_instruction), "gemini"
        except Exception as exc:
            logger.warning(
                "Gemini chat completion failed; falling back to light model: %s",
                exc,
                exc_info=True,
            )
    if not settings.llm_api_key_configured:
        raise ValueError(
            "Neither GEMINI_API_KEY nor LLM_API_KEY is set (or LLM key is placeholder); "
            "cannot complete chat request.",
        )
    text = llm_chat_completion(
        model=settings.light_model,
        user_message=user_message,
        system_instruction=system_instruction,
        max_tokens=max_tokens,
    )
    return text, "light_model"


def gemini_or_light_chat_completion(
    user_message: str,
    system_instruction: str | None = None,
    *,
    max_tokens: int = 800,
) -> str:
    """Prefer Gemini when configured; on failure, use ``LIGHT_MODEL`` (see ``gemini_or_light_chat_completion_pair``)."""
    text, _ = gemini_or_light_chat_completion_pair(
        user_message,
        system_instruction,
        max_tokens=max_tokens,
    )
    return text


def gemini_or_light_chat_with_messages(
    messages: list[tuple[str, str]],
    system_instruction: str | None = None,
    *,
    max_tokens: int = 4096,
) -> str:
    """Multi-turn: Gemini when configured, else ``LIGHT_MODEL`` via OpenAI-compat API."""
    if settings.gemini_api_key_configured:
        try:
            return gemini_chat_with_messages(messages, system_instruction)
        except Exception as exc:
            logger.warning(
                "Gemini multi-turn chat failed; falling back to light model: %s",
                exc,
                exc_info=True,
            )
    if not settings.llm_api_key_configured:
        raise ValueError(
            "Neither GEMINI_API_KEY nor LLM_API_KEY is set (or LLM key is placeholder); "
            "cannot complete chat request.",
        )
    return llm_chat_with_messages(
        messages,
        system_instruction,
        model=settings.light_model,
        max_tokens=max_tokens,
    )


def gemini_chat_with_messages(
    messages: list[tuple[str, str]],
    system_instruction: str | None = None,
) -> str:
    """
    Multi-turn Gemini chat. Each tuple is (role, text) where role is \"user\" or \"model\".
    """
    if not settings.gemini_api_key_configured:
        raise ValueError("GEMINI_API_KEY is not set in apps/api/.env")

    model = (settings.gemini_model or "gemini-2.5-flash").strip()
    url = GEMINI_GENERATE_URL.format(model=model)
    params = {"key": settings.gemini_api_key.strip()}

    contents: list[dict[str, Any]] = []
    for role, text in messages:
        r = "user" if role == "user" else "model"
        contents.append({"role": r, "parts": [{"text": text}]})

    body: dict[str, Any] = {"contents": contents}
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, params=params, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Gemini API error {resp.status_code}: {resp.text[:2000]}",
            )
        data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:1500]}")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
    return "".join(texts).strip() or "(empty model response)"


def elevenlabs_synthesize_mp3(text: str, voice_id: str | None = None) -> bytes:
    if not settings.elevenlabs_api_key_configured:
        raise ValueError("ELEVENLABS_API_KEY is not set in apps/api/.env")

    env_voice = (settings.elevenlabs_voice_id or "").strip()
    vid = (voice_id or env_voice or DEFAULT_ELEVENLABS_VOICE_ID).strip()
    url = ELEVENLABS_TTS_URL.format(voice_id=vid)
    headers = {
        "xi-api-key": settings.elevenlabs_api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    # Insight podcast scripts can be ~250–350 words; cap under typical TTS request limits.
    max_chars = min(len(text), 5000)
    payload = {
        "text": text[:max_chars],
        "model_id": "eleven_multilingual_v2",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"ElevenLabs API error {resp.status_code}: {resp.text[:2000]}",
            )
        return resp.content
