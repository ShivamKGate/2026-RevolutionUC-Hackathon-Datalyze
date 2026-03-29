"""LLM-backed short titles for completed analyses."""

from __future__ import annotations

import logging
import re
from typing import Any

from core.config import settings
from services.external_agent_clients import gemini_chat_completion, llm_chat_completion

logger = logging.getLogger(__name__)


def _strip_title(raw: str) -> str:
    t = (raw or "").strip()
    t = re.sub(r'^["\']|["\']$', "", t).strip()
    return t[:500]


def _artifact_primary_payload(artifacts: list[Any]) -> dict[str, Any]:
    """Same shape as engine._artifact_primary_payload (avoid circular import)."""
    for block in artifacts or []:
        if not isinstance(block, dict):
            continue
        for key in ("data", "result"):
            inner = block.get(key)
            if isinstance(inner, dict) and inner:
                return inner
    return {}


def _executive_blobs_from_replay(ar: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (flat_envelope_fields, structured_from_artifacts) for executive_summary agent."""
    ex = ar.get("executive_summary") or {}
    if not isinstance(ex, dict):
        return {}, {}
    arts = ex.get("artifacts") or []
    structured = _artifact_primary_payload(arts) if arts else {}
    if not isinstance(structured, dict):
        structured = {}
    return ex, structured


def _headline_overview_track(replay_payload: dict[str, Any]) -> tuple[str, str, str]:
    ar = replay_payload.get("agent_results") or {}
    if not isinstance(ar, dict):
        ar = {}
    ex, structured = _executive_blobs_from_replay(ar)
    headline = str(structured.get("headline") or ex.get("headline") or "").strip()
    overview = str(
        structured.get("situation_overview") or ex.get("situation_overview") or "",
    ).strip()[:1500]
    fr = replay_payload.get("final_report") or {}
    track = str(fr.get("track") or "") if isinstance(fr, dict) else ""
    track = track.strip()
    return headline, overview, track


def _fallback_title(headline: str, overview: str, track: str) -> str:
    if headline:
        return _strip_title(headline)
    snippet = (overview or "").replace("\n", " ").strip()
    if len(snippet) > 72:
        snippet = snippet[:69] + "…"
    if snippet and track:
        return _strip_title(f"{track.replace('_', ' ').title()}: {snippet}")
    if snippet:
        return _strip_title(snippet)
    if track:
        return _strip_title(f"{track.replace('_', ' ').title()} analysis")
    return ""


def propose_analysis_title_from_replay_payload(replay_payload: dict[str, Any]) -> str:
    """One-line title: light LLM when configured, else Gemini, else headline / heuristic."""
    headline, overview, track = _headline_overview_track(replay_payload)
    user_msg = (
        f"Analysis track: {track or 'unknown'}\n"
        f"Executive headline: {headline or '(none)'}\n"
        f"Situation overview (excerpt):\n{overview or '(none)'}\n\n"
        "Reply with exactly one concise title (maximum 12 words). "
        "No quotation marks. No trailing period. Title case or sentence case is fine."
    )
    system = "You name business analyses for dashboards. Output only the title, nothing else."

    if settings.llm_api_key_configured:
        try:
            raw = llm_chat_completion(
                settings.light_model,
                user_msg,
                system,
                max_tokens=64,
            )
            t = _strip_title(raw)
            if t and t != "(empty model response)":
                return t
        except Exception as e:
            logger.warning("Title LLM (Featherless/light) failed: %s", e)

    if settings.gemini_api_key_configured:
        try:
            raw = gemini_chat_completion(user_msg, system)
            t = _strip_title(raw)
            if t and t != "(empty model response)":
                return t
        except Exception as e:
            logger.warning("Title LLM (Gemini) failed: %s", e)

    return _fallback_title(headline, overview, track)
