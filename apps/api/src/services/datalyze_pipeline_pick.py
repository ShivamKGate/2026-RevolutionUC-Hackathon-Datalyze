"""
Pick predictive / automation / optimization / supply_chain for Datalyze custom runs
when the user selects Auto — uses conversation + file metadata (+ public-scrape flag).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy import text

from db.session import SessionLocal
from services.external_agent_clients import gemini_or_light_chat_completion

logger = logging.getLogger("datalyze_pipeline_pick")

_VALID = frozenset({"predictive", "automation", "optimization", "supply_chain"})

_PIPELINE_PICK_SYSTEM = """You route a custom Datalyze analysis to exactly ONE base pipeline.

Pipeline ids (choose one):
- predictive — KPI/trend forecasting, time series, projections, risk bands, market/sentiment signals tied to forward outlook
- automation — DevOps, process bottlenecks, workflow automation, integration/RPA-style opportunities, operational handoffs
- optimization — business operations efficiency, org-wide cost/process improvement, strategic ops (not primarily logistics network)
- supply_chain — logistics, inventory, suppliers, lead times, fulfillment, network delays, resilience

Signals to use:
- The user’s stated goal in the conversation (custom analysis instruction).
- File names, MIME types, and any upload-track hints listed below.
- If public_scrape is true, external/public data may augment the run (benchmarks, industry context) — slight tilt toward predictive or supply_chain when the user asks for external comparison or market context.

Respond with a single JSON object only (no markdown):
{"pipeline":"<predictive|automation|optimization|supply_chain>","rationale":"<one concise sentence>"}"""


def _extract_json_object(s: str) -> dict[str, Any]:
    t = (s or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", t)
    if m:
        return json.loads(m.group(0))
    raise ValueError("no json object")


def normalize_pipeline_id(raw: str | None) -> str:
    s = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "deep_analysis": "predictive",
        "trend": "predictive",
        "forecast": "predictive",
        "devops": "automation",
        "automations": "automation",
        "business_automations": "optimization",
        "business": "optimization",
        "ops": "optimization",
        "logistics": "supply_chain",
        "inventory": "supply_chain",
    }
    s = aliases.get(s, s)
    if s in _VALID:
        return s
    return "predictive"


def _file_hints_for_ids(company_id: int, file_ids: list[int]) -> str:
    if not file_ids:
        return "(no files selected)"
    uniq = sorted(set(int(x) for x in file_ids))
    in_clause = ",".join(str(i) for i in uniq)
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                f"SELECT id, original_filename, content_type, analysis_track, byte_size, visibility "
                f"FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause}) ORDER BY id ASC"
            ),
            {"cid": company_id},
        ).fetchall()
    finally:
        db.close()
    if not rows:
        return "(file ids not found in library)"
    lines = []
    for r in rows:
        lines.append(
            f"- id={r.id} name={r.original_filename!r} mime={r.content_type!r} "
            f"upload_track={r.analysis_track!r} visibility={r.visibility!r} bytes={r.byte_size}",
        )
    return "\n".join(lines)


def pick_custom_base_track(
    *,
    company_id: int,
    company_name: str,
    conversation_transcript: str,
    uploaded_file_ids: list[int],
    public_scrape_enabled: bool,
) -> tuple[str, str]:
    """
    Returns (pipeline_id, rationale) for orchestrator custom_base_track.
    On any failure, falls back to predictive with a generic rationale.
    """
    hints = _file_hints_for_ids(company_id, uploaded_file_ids)
    user_block = (
        f"company_name: {company_name}\n"
        f"public_scrape_enabled: {public_scrape_enabled}\n\n"
        f"--- File hints ---\n{hints}\n\n"
        f"--- Conversation ---\n{conversation_transcript}\n"
    )
    try:
        raw = gemini_or_light_chat_completion(
            user_block,
            _PIPELINE_PICK_SYSTEM,
            max_tokens=450,
        )
        data = _extract_json_object(raw)
        pid = normalize_pipeline_id(str(data.get("pipeline", "")))
        rationale = str(data.get("rationale") or "").strip() or f"Routed to {pid}."
        logger.info(
            "datalyze auto pipeline: %s (%s)",
            pid,
            rationale[:120],
        )
        return pid, rationale
    except Exception as e:
        logger.warning("datalyze auto pipeline pick failed: %s", e, exc_info=True)
        return "predictive", f"Auto-routing defaulted to predictive ({e})."
