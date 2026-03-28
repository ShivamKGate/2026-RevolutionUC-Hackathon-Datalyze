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


def openai_compat_chat_completion(
    model: str,
    user_message: str,
    system_instruction: str | None = None,
) -> str:
    is_ollama = settings.llm_provider == "ollama"
    if not is_ollama and not settings.llm_api_key_configured:
        raise ValueError("LLM_API_KEY is not set in apps/api/.env")

    base = settings.llm_base_url.rstrip("/")
    if is_ollama and not base.endswith("/v1"):
        base = f"{base}/v1"
    url = f"{base}/chat/completions"
    messages: list[dict[str, str]] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": user_message})

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 80,
    }

    headers = {"Content-Type": "application/json"}
    if not is_ollama:
        headers["Authorization"] = f"Bearer {settings.llm_api_key.strip()}"

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"OpenAI-compat API error {resp.status_code}: {resp.text[:2000]}",
            )
        data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenAI-compat returned no choices: {json.dumps(data)[:1500]}")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    return content or "(empty model response)"


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

    vid = (voice_id or DEFAULT_ELEVENLABS_VOICE_ID).strip()
    url = ELEVENLABS_TTS_URL.format(voice_id=vid)
    headers = {
        "xi-api-key": settings.elevenlabs_api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text[:2500],
        "model_id": "eleven_multilingual_v2",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"ElevenLabs API error {resp.status_code}: {resp.text[:2000]}",
            )
        return resp.content
