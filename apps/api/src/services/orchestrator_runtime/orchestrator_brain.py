"""
Heavy-model orchestration layer — the programmatic "orchestrator agent" brain.

Always calls **only** ``settings.heavy_model`` (``HEAVY_MODEL`` in ``apps/api/.env``),
e.g. ``moonshotai/Kimi-K2.5``. Same source as the registry's heavy / orchestrator
slot; not ``HEAVY_ALT_MODEL`` or ``LIGHT_MODEL``.

Runs once after pipeline classification to refine skip_agents, emit a shared
orchestrator brief for downstream agents, and optional per-agent guidance.

This complements the Gemini classifier: the heavy model reasons over the full
track + classifier JSON + file hints for context-rich routing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from core.config import settings

logger = logging.getLogger("orchestrator")

# Agents the brain must never mark skipped (core path + mandatory synthesis).
_SKIP_DENYLIST = frozenset({
    "orchestrator",
    "pipeline_classifier",
    "file_type_classifier",
    "data_cleaning",
    "smart_categorizer_metadata",
    "aggregator",
    "insight_generation",
    "executive_summary",
})

# Only these may be added as skips by the heavy model (analyze / optional / scrape).
_SKIP_ALLOWLIST = frozenset({
    "public_data_scraper",
    "conflict_detection",
    "trend_forecasting",
    "sentiment_analysis",
    "knowledge_graph_builder",
    "automation_strategy",
    "swot_analysis",
    "elevenlabs_narration",
})


def _try_parse_json_object(raw: str) -> dict[str, Any] | None:
    s = (raw or "").strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```\s*$", "", s)
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", s)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _sanitize_skip_agents(candidates: list[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for x in candidates:
        if not isinstance(x, str):
            continue
        aid = x.strip()
        if not aid or aid in seen:
            continue
        if aid in _SKIP_DENYLIST:
            continue
        if aid not in _SKIP_ALLOWLIST:
            continue
        seen.add(aid)
        out.append(aid)
    return out


def _sanitize_guidance(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        ks = k.strip()
        vs = v.strip()
        if ks and vs and len(vs) < 2000:
            out[ks] = vs[:1200]
    return out


def _registry_agent_lines() -> list[str]:
    from services.agent_registry import get_registry

    reg = get_registry()
    lines: list[str] = []
    for spec in reg.specs:
        if spec.id in ("orchestrator", "data_provenance_tracker", "natural_language_search"):
            continue
        lines.append(
            f"- {spec.id}: {spec.responsibilities[:220]}",
        )
    return lines


def _brain_payload_empty() -> dict[str, Any]:
    return {
        "skip_agents": [],
        "orchestrator_brief": "",
        "per_agent_guidance": {},
        "heavy_model": settings.heavy_model,
    }


def run_heavy_orchestration_brain(
    *,
    track: str,
    company_name: str,
    onboarding_path: str,
    source_files_meta: list[dict[str, Any]],
    classifier_result: dict[str, Any],
    focus_agents: list[str],
) -> dict[str, Any]:
    """Call ``HEAVY_MODEL`` only to refine routing and produce a shared context brief.

    Returns a dict with keys: skip_agents, orchestrator_brief, per_agent_guidance,
    heavy_model (echo of ``settings.heavy_model`` from env).

    On failure or when disabled, returns the same shape with empty skips/brief.
    """
    empty = _brain_payload_empty()

    if not settings.orch_heavy_brain_enabled:
        return empty
    if not settings.llm_api_key_configured:
        logger.info("Heavy orchestration brain skipped: LLM_API_KEY not configured")
        return empty

    roster = "\n".join(_registry_agent_lines()[:80])
    clf = json.dumps(classifier_result, ensure_ascii=False, indent=2)[:12000]
    files_hint = json.dumps(source_files_meta or [], ensure_ascii=False)[:4000]
    focus = ", ".join(focus_agents) if focus_agents else "(none)"

    user_message = (
        "You are the central orchestration brain for a multi-agent business analysis pipeline.\n"
        "A lightweight classifier (Gemini) already chose a track and proposed skip_agents / "
        "recommended_agents. Your job is to refine routing using the HEAVY model: decide which "
        "optional and analysis agents are worth running for THIS run, and produce rich context "
        "so every downstream agent produces specific, evidence-grounded output.\n\n"
        f"Company: {company_name}\n"
        f"Track: {track}\n"
        f"User goal / onboarding: {onboarding_path or '(not provided)'}\n"
        f"Track focus agents (hints): {focus}\n\n"
        f"Classifier output (JSON):\n{clf}\n\n"
        f"File metadata (may be empty):\n{files_hint}\n\n"
        "AGENT ROSTER (registry):\n"
        f"{roster}\n\n"
        "RULES:\n"
        "- Do NOT skip core path agents: file_type_classifier, processors (when files exist), "
        "data_cleaning, smart_categorizer_metadata, aggregator, insight_generation, "
        "executive_summary.\n"
        "- You MAY skip optional analysis/synthesis agents when they add little value for this "
        f"run. Only use these agent_ids in skip_agents: {sorted(_SKIP_ALLOWLIST)}.\n"
        "- If the classifier already listed skip_agents, you may keep, narrow, or extend that "
        "list — justify changes in orchestrator_brief.\n"
        "- Prefer fewer agents when goals are narrow; use more when the user needs breadth.\n"
        "- orchestrator_brief must be 3–6 short paragraphs: company + track context, what matters "
        "for this run, which angles to emphasize, data caveats, and what NOT to claim without "
        "evidence.\n"
        "- per_agent_guidance: optional map agent_id -> one or two sentences of tailored "
        "instruction for that agent only (empty object if unsure).\n\n"
        "Respond with ONLY a JSON object:\n"
        "{\n"
        '  "skip_agents": ["agent_id", ...],\n'
        '  "orchestrator_brief": "string",\n'
        '  "per_agent_guidance": {"agent_id": "string", ...}\n'
        "}\n"
    )

    # Sole orchestrator-brain model: HEAVY_MODEL from .env (never heavy_alt / light).
    orchestrator_model = settings.heavy_model

    try:
        from services.external_agent_clients import llm_chat_completion

        raw = llm_chat_completion(
            model=orchestrator_model,
            user_message=user_message,
            system_instruction=(
                "You are the Datalyze orchestration brain. You output only valid JSON. "
                "You never skip mandatory pipeline agents. You maximize insight quality by "
                "steering optional agents and rich shared context."
            ),
            max_tokens=2500,
        )
    except Exception as exc:
        logger.warning("Heavy orchestration brain LLM call failed: %s", exc)
        return empty

    parsed = _try_parse_json_object(raw)
    if not parsed:
        logger.warning("Heavy orchestration brain returned non-JSON")
        return empty

    skip_raw = parsed.get("skip_agents")
    skips = _sanitize_skip_agents(skip_raw if isinstance(skip_raw, list) else [])

    brief = parsed.get("orchestrator_brief")
    brief_s = brief.strip() if isinstance(brief, str) else ""
    if len(brief_s) > 8000:
        brief_s = brief_s[:8000]

    guidance = _sanitize_guidance(parsed.get("per_agent_guidance"))

    return {
        "skip_agents": skips,
        "orchestrator_brief": brief_s,
        "per_agent_guidance": guidance,
        "heavy_model": orchestrator_model,
    }


def merge_skip_agent_lists(*lists: list[str] | None) -> list[str]:
    """Merge skip lists from classifier + heavy brain; preserve order, dedupe."""
    out: list[str] = []
    seen: set[str] = set()
    for lst in lists:
        for x in lst or []:
            if not isinstance(x, str):
                continue
            s = x.strip()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
    return out
