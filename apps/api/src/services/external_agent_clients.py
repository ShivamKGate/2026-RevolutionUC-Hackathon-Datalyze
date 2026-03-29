"""
Direct HTTP clients for sponsor APIs used by registry agents:

- pipeline_classifier / gemini_api → Gemini generateContent
- image_multimodal_processor / gemini_vision → same Gemini model (multimodal-capable)
- elevenlabs_narration → ElevenLabs text-to-speech
"""

from __future__ import annotations

import json

import httpx

from core.config import settings

GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
# Default voice (Rachel) — override via ELEVENLABS_VOICE_ID in env if we add it later
DEFAULT_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


def normalize_openai_compat_model_slug(model: str) -> str:
    """Same routing as CrewAI/registry: org/model slugs need an openai/ prefix for Featherless."""
    normalized = (model or "").strip()
    if not normalized:
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
