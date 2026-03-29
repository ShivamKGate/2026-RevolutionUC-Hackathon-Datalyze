"""
LLM gate for Datalyze Chat: conversational replies and optional custom-analysis kickoff.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from schemas.files_runs import (
    DatalyzeChatRequest,
    DatalyzeChatResponse,
    PipelineRunOut,
    StartPipelineRunRequest,
)
from services.datalyze_pipeline_pick import pick_custom_base_track
from services.external_agent_clients import gemini_or_light_chat_completion

logger = logging.getLogger("datalyze_chat")

DATALYZE_CHAT_SYSTEM = """You are Datalyze Chat, an assistant for the Datalyze analytics product.

The user may attach company data files and optionally enable public web scraping for their company context.

Your job:
1. Have a helpful, concise conversation about data analysis, KPIs, forecasting, automation opportunities, supply-chain signals, and comparisons — aligned with what Datalyze pipelines produce.
2. Only set "start_analysis": true when the user clearly wants a NEW full pipeline run (report, deep analysis, compare datasets, trend study, etc.) that fits this product. Do NOT start for greetings, small talk, or questions answerable without a new run.
3. If the request is out of scope (e.g. unrelated coding homework), refuse politely and set "start_analysis": false.

Reply MUST be a single JSON object with this exact shape (no markdown fences):
{
  "reply": "string — what you say to the user",
  "start_analysis": false,
  "start_reason": "optional short reason when start_analysis is true"
}

When "start_analysis" is true, the backend will queue a custom analysis run (same orchestrator as standard analyses) using their selected files and settings."""


def _extract_json_object(text: str) -> dict[str, Any]:
    t = (text or "").strip()
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
    raise ValueError("No JSON object in model output")


def datalyze_turn(
    *,
    user: dict,
    body: DatalyzeChatRequest,
    execute_pipeline_start,
    require_company,
) -> DatalyzeChatResponse:
    """
    `execute_pipeline_start` is `api.v1.routes.runs.execute_pipeline_start` injected to avoid import cycles.
    `require_company` is `api.v1.routes.runs._require_company`.
    """
    msgs = body.messages[-24:]
    if not msgs:
        return DatalyzeChatResponse(reply="Ask a question or request a custom analysis.", started_run=None)

    transcript = "\n".join(
        f"{'user' if m.role == 'user' else 'assistant'}: {m.content}" for m in msgs
    )
    prompt = (
        f"{transcript}\n\n"
        "Remember: respond with one JSON object only, per system rules."
    )

    try:
        raw = gemini_or_light_chat_completion(
            prompt,
            DATALYZE_CHAT_SYSTEM,
            max_tokens=2048,
        )
        data = _extract_json_object(raw)
    except Exception as e:
        logger.warning("datalyze chat LLM failed: %s", e, exc_info=True)
        return DatalyzeChatResponse(
            reply=(
                "Could not reach a language model. Set GEMINI_API_KEY and/or LLM_API_KEY "
                "in apps/api/.env and try again."
            ),
            started_run=None,
        )

    reply = str(data.get("reply") or "").strip() or "OK."
    start = bool(data.get("start_analysis"))

    if not start:
        return DatalyzeChatResponse(reply=reply, started_run=None)

    ids = [int(x) for x in body.uploaded_file_ids]
    scrape = bool(body.enable_public_scrape)
    if not ids and not scrape:
        return DatalyzeChatResponse(
            reply=(
                f"{reply}\n\nTo run a custom analysis, select at least one uploaded file "
                "or enable public scraping (if your company allows it)."
            ),
            started_run=None,
        )

    company_id, company_name = require_company(user)
    base_raw = (body.custom_base_track or "auto").strip().lower()
    pipeline_rationale: str | None = None
    user_instruction = ""
    for m in reversed(body.messages):
        if (m.role or "").strip().lower() == "user" and (m.content or "").strip():
            user_instruction = (m.content or "").strip()[:4000]
            break

    if base_raw == "auto":
        base, pipeline_rationale = pick_custom_base_track(
            company_id=company_id,
            company_name=company_name or "company",
            conversation_transcript=transcript,
            uploaded_file_ids=ids,
            public_scrape_enabled=scrape,
        )
    else:
        allowed = {"predictive", "automation", "optimization", "supply_chain"}
        base = base_raw if base_raw in allowed else "predictive"

    try:
        run_out: PipelineRunOut = execute_pipeline_start(
            user,
            StartPipelineRunRequest(
                uploaded_file_ids=ids,
                onboarding_path="Datalyze Chat",
                force_new=True,
                public_scrape_enabled=scrape,
                custom_base_track=base,
                pipeline_selection_rationale=pipeline_rationale,
                datalyze_user_instruction=user_instruction or None,
            ),
        )
    except Exception as e:
        logger.warning("datalyze chat start run failed: %s", e, exc_info=True)
        return DatalyzeChatResponse(
            reply=f"{reply}\n\nCould not start the analysis: {e}",
            started_run=None,
        )

    route_line = (
        (
            f"\n\nUsing the {base.replace('_', ' ')} pipeline shape"
            + (f" — {pipeline_rationale}" if pipeline_rationale else "")
            + "."
        )
        if base_raw == "auto"
        else ""
    )
    return DatalyzeChatResponse(
        reply=(
            f"{reply}{route_line}\n\nQueued a new custom analysis run ({run_out.slug}). "
            "Open it from the dashboard."
        ),
        started_run=run_out,
    )
