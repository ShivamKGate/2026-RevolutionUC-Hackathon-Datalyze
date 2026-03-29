"""
Orchestrator engine: the core execution loop that replaces placeholder runs.

Chooses and dispatches every agent step. All agent calls return to the
orchestrator -- agents never self-chain. Uses the AgentExecutionAdapter
to call agents through the registry and normalize outputs to AgentEnvelope.

Integration note for Shivam's specialization branch:
  The adapter dispatch calls registry agents and wraps their output.
  When per-agent modules are merged, update _dispatch_agent() to call
  the specialized task template instead of the generic CrewAI kickoff.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import settings
from services.agent_registry import get_registry
from services.orchestrator_runtime.contracts import (
    AgentEnvelope,
    DecisionRecord,
    MemoryState,
    RunManifest,
    RunStatus,
    StageGateResult,
    StageID,
)
from services.orchestrator_runtime.orchestrator_brain import (
    merge_skip_agent_lists,
    run_heavy_orchestration_brain,
)
from services.orchestrator_runtime.persistence import (
    append_decision,
    db_capture_demo_replay,
    db_find_latest_matching_completed_run,
    db_insert_artifacts,
    db_insert_run_log,
    db_update_run_status,
    update_artifacts_index,
    write_agent_output,
    write_context_index,
    write_final_report,
    write_input_metadata,
    write_manifest,
    write_memory,
    write_quality_gate,
)
from services.orchestrator_runtime.policies import (
    check_time_budget,
    classify_completion,
    evaluate_retry,
    evaluate_stage_gate,
    generate_fix_suggestions,
    pick_next_agents,
)
from services.orchestrator_runtime.cancellation import (
    clear_cancel_request,
    is_cancel_requested,
)
from services.orchestrator_runtime.track_profiles import (
    TrackID,
    get_track_profile,
    resolve_track,
)
from services.run_paths import create_run_directory, run_dir_relative

logger = logging.getLogger("orchestrator")

_GENERIC_OUTPUT_PHRASES = frozenset({
    "completed", "done", "ok", "success", "finished", "complete",
    "task completed", "analysis complete", "analysis done",
})


def _is_minimal_output(envelope: AgentEnvelope) -> bool:
    """Return True if the envelope summary is too thin to be actionable."""
    summary = (envelope.summary or "").strip()
    return len(summary) < 20 or summary.lower() in _GENERIC_OUTPUT_PHRASES


def _needed_processors_from_ftc_result(ftc_result: dict[str, Any]) -> set[str]:
    """Collect processor agent IDs from file_type_classifier JSON (map or file_routing list)."""
    needed: set[str] = set()
    m = ftc_result.get("file_routing_map")
    if isinstance(m, dict):
        for v in m.values():
            if isinstance(v, str) and v.strip():
                needed.add(v.strip())
    rows = ftc_result.get("file_routing")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                p = row.get("processor")
                if isinstance(p, str) and p.strip():
                    needed.add(p.strip())
    return needed


def _normalize_classifier_track(raw: str | None, onboarding_path: str) -> str:
    t = (raw or "").strip().lower().replace("-", "_")
    valid = {x.value for x in TrackID}
    if t in valid:
        return t
    return resolve_track(onboarding_path).value


def _classifier_routing_defaults(canonical_track: str) -> tuple[list[str], list[str]]:
    """Default skip_agents / recommended_agents when the LLM omits them."""
    try:
        tid = TrackID(canonical_track)
    except ValueError:
        tid = TrackID.PREDICTIVE
    profile = get_track_profile(tid)
    recommended = list(profile.focus_agents)
    skip: list[str] = []
    if tid in (TrackID.PREDICTIVE, TrackID.OPTIMIZATION, TrackID.SUPPLY_CHAIN):
        skip = ["automation_strategy"]
    return skip, recommended


def _finalize_classifier_result(parsed: dict[str, Any], onboarding_path: str) -> dict[str, Any]:
    nt = _normalize_classifier_track(parsed.get("track"), onboarding_path)
    merged = {**parsed, "track": nt}
    d_skip, d_rec = _classifier_routing_defaults(nt)
    if not merged.get("skip_agents"):
        merged["skip_agents"] = d_skip
    if not merged.get("recommended_agents"):
        merged["recommended_agents"] = d_rec
    return merged


def _artifact_primary_payload(artifacts: list[Any]) -> dict[str, Any]:
    """First dict payload from agent artifacts (result or data / agent_output)."""
    if not artifacts or not isinstance(artifacts[0], dict):
        return {}
    block = artifacts[0]
    for key in ("result", "data"):
        v = block.get(key)
        if isinstance(v, dict):
            return v
    return {}


def _try_parse_executive_json(raw: str) -> dict[str, Any] | None:
    """Parse executive-summary JSON from model output (may include fences or prose)."""
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


def _format_executive_dict_for_speech(data: dict[str, Any], max_chars: int = 2400) -> str:
    """Flatten structured executive summary into spoken prose."""
    parts: list[str] = []
    if h := data.get("headline"):
        parts.append(str(h).strip())
    if s := data.get("situation_overview"):
        parts.append(str(s).strip())
    kf = data.get("key_findings")
    if isinstance(kf, list) and kf:
        parts.append(
            "Key findings: " + ". ".join(str(x).strip() for x in kf[:10] if x),
        )
    rh = data.get("risk_highlights")
    if isinstance(rh, list) and rh:
        parts.append(
            "Risk highlights: " + ". ".join(str(x).strip() for x in rh[:6] if x),
        )
    na = data.get("next_actions")
    if isinstance(na, list) and na:
        parts.append(
            "Next actions: " + ". ".join(str(x).strip() for x in na[:8] if x),
        )
    cs = data.get("confidence_statement")
    if isinstance(cs, dict):
        oc = cs.get("overall_confidence")
        basis = (cs.get("basis") or "").strip()
        if oc is not None or basis:
            conf_bit = f"Confidence: {oc}." if oc is not None else ""
            parts.append(f"{conf_bit} {basis}".strip())
    out = " ".join(p for p in parts if p)
    return out[:max_chars] if len(out) > max_chars else out


def _format_summary_text_for_tts(raw: str) -> str:
    """Normalize markdown-fenced or JSON executive summary for speech synthesis."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    parsed = _try_parse_executive_json(raw)
    if parsed:
        spoken = _format_executive_dict_for_speech(parsed)
        if spoken:
            return spoken
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    return cleaned.strip()


def _resolve_executive_summary_text(context: dict[str, Any]) -> str:
    """Text for ElevenLabs: explicit field, then prior_outputs executive_summary envelope."""
    direct = (context.get("executive_summary") or "").strip()
    if direct:
        return _format_summary_text_for_tts(direct)

    prior = context.get("prior_outputs") or {}
    env = prior.get("executive_summary")
    if not isinstance(env, dict):
        return ""

    raw_summary = (env.get("summary") or "").strip()
    if raw_summary:
        spoken = _format_summary_text_for_tts(raw_summary)
        if spoken:
            return spoken

    arts = env.get("artifacts") or []
    structured = _artifact_primary_payload(arts) if arts else {}
    if isinstance(structured, dict) and structured:
        return _format_executive_dict_for_speech(structured)
    return ""


def _word_count_spoken(s: str) -> int:
    return len([w for w in (s or "").split() if w.strip()])


def _strip_podcast_script(raw: str) -> str:
    """Remove accidental fences or labels from LLM output."""
    t = (raw or "").strip()
    t = re.sub(r"^```(?:\w*)?\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"\s*```\s*$", "", t)
    t = re.sub(r"^(?:Podcast script|Script|Transcript)\s*:\s*", "", t, flags=re.IGNORECASE)
    return t.strip()


def _build_podcast_source_material(context: dict[str, Any]) -> str:
    """Aggregate executive summary + key structured agent outputs for podcast script LLM."""
    chunks: list[str] = []
    prior = context.get("prior_outputs") or {}
    company = context.get("company_name", "Unknown Company")
    track = context.get("track", "predictive")

    exec_flat = _resolve_executive_summary_text(context)
    if exec_flat:
        chunks.append(f"--- Executive synthesis (verbatim) ---\n{exec_flat[:6000]}")

    structured = _collect_structured_outputs(prior)
    priority = (
        "insight_generation",
        "swot_analysis",
        "trend_forecasting",
        "conflict_detection",
        "sentiment_analysis",
        "executive_summary",
        "aggregator",
        "automation_strategy",
    )
    for aid in priority:
        blob = structured.get(aid)
        if not isinstance(blob, dict) or not blob:
            continue
        try:
            compact = json.dumps(blob, ensure_ascii=False)[:3500]
        except (TypeError, ValueError):
            compact = str(blob)[:3500]
        chunks.append(f"--- {aid} (structured JSON) ---\n{compact}")

    for aid, env in prior.items():
        if aid in (
            "elevenlabs_narration",
            "pipeline_classifier",
            "output_evaluator",
        ):
            continue
        if aid in structured:
            continue
        summ = (env.get("summary") or "").strip()
        if 120 < len(summ) < 2000:
            chunks.append(f"--- {aid} (agent summary) ---\n{summ[:1800]}")

    body = "\n\n".join(chunks)
    header = f"Company: {company}. Analysis track: {track}.\n\n"
    return (header + body)[:14000]


def _generate_podcast_script_via_llm(context: dict[str, Any]) -> str:
    """Synthesize a 1–1.5 minute spoken podcast script from analysis outputs."""
    if not settings.llm_api_key_configured:
        return ""

    source = _build_podcast_source_material(context)
    if not source.strip():
        return ""

    company = context.get("company_name", "this company")
    track = context.get("track", "analysis")

    from services.external_agent_clients import llm_chat_completion

    user_message = (
        "Write a single continuous podcast monologue for listeners who want a spoken briefing "
        "on a business analysis run.\n\n"
        "SOURCE MATERIAL (fragments, JSON, and summaries — synthesize into one coherent story):\n"
        f"{source}\n\n"
        "STRICT RULES:\n"
        "- Output ONLY the words to be read aloud by a text-to-speech voice.\n"
        "- No markdown, no bullet characters, no section headers, no stage directions, "
        "no 'host:', no music cues, no timestamps.\n"
        "- Length: between 240 and 320 words (about 1 to 1.5 minutes at normal speaking pace). "
        "Do not exceed 320 words.\n"
        "- Open with one or two engaging sentences that welcome the listener and name the company "
        f"and that this is the {track} analysis insights.\n"
        "- Weave together the most important findings, tradeoffs, risks, and opportunities from the source.\n"
        "- Include concrete next actions or recommendations when the source material supports them.\n"
        "- Do not invent numbers, companies, or facts not present or clearly implied in the source.\n"
        "- Close with one short memorable sign-off (one sentence).\n"
        "- Use plain sentences; vary rhythm so it sounds natural when spoken.\n"
    )

    try:
        raw = llm_chat_completion(
            model=settings.heavy_alt_model or settings.heavy_model,
            user_message=user_message,
            system_instruction=(
                "You write only spoken podcast scripts for business intelligence. "
                "You never add preamble or commentary outside the script."
            ),
            max_tokens=1100,
        )
    except Exception as exc:
        logger.warning("Podcast script LLM call failed: %s", exc)
        return ""

    script = _strip_podcast_script(raw)
    wc = _word_count_spoken(script)
    if wc < 120:
        logger.warning(
            "Podcast script too short (%s words, need ~120+); will use fallback", wc,
        )
        return ""
    if wc > 380:
        # Hard cap so TTS stays ~1.5 min; trim at sentence boundary near 320 words
        words = script.split()
        script = " ".join(words[:320])
    return script


def _collect_structured_outputs(
    prior_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Map agent_id → parsed JSON dict for output_evaluator / UI."""
    out: dict[str, Any] = {}
    for aid, env in prior_outputs.items():
        arts = env.get("artifacts") or []
        for block in arts:
            if not isinstance(block, dict):
                continue
            for key in ("data", "result"):
                inner = block.get(key)
                if isinstance(inner, dict) and inner:
                    out[aid] = inner
                    break
            if aid in out:
                break
    return out


def _build_dependency_map() -> dict[str, list[str]]:
    """Extract agent dependency graph from registry specs."""
    registry = get_registry()
    # "orchestrator" is the controller, not a dispatchable dependency node.
    return {
        spec.id: [dep for dep in spec.dependencies if dep != "orchestrator"]
        for spec in registry.specs
    }


def _dispatch_agent(
    agent_id: str,
    context: dict[str, Any],
    run_dir: Path,
) -> AgentEnvelope:
    """Dispatch a single agent and return normalized envelope.

    This is the adapter boundary. Currently uses registry CrewAI agents
    with a generic task prompt. When Shivam's per-agent modules are
    merged, this function should delegate to the specialized task
    template factory instead.
    """
    registry = get_registry()
    if not registry.nodes:
        registry.initialize()
    node = registry.nodes.get(agent_id)

    if node is None:
        return AgentEnvelope.error_envelope(f"Agent {agent_id} not found in registry")

    if not node.initialized:
        return AgentEnvelope.warning_envelope(
            f"Agent {agent_id} not initialized, skipping"
        )

    # External service agents use direct API calls
    if node.runtime_kind == "external-service":
        return _dispatch_external_agent(agent_id, context)

    # System layer agents produce internal metadata
    if node.runtime_kind == "system-layer":
        return _dispatch_system_agent(agent_id, context)

    # CrewAI-based agents: build task prompt from context and dispatch
    return _dispatch_crewai_agent(agent_id, node, context)


def _dispatch_crewai_agent(
    agent_id: str,
    node: Any,
    context: dict[str, Any],
) -> AgentEnvelope:
    """Dispatch a CrewAI agent with context-aware task prompt."""
    try:
        from crewai import Task, Crew

        task_description = _build_task_prompt(agent_id, node.spec, context)
        task = Task(
            description=task_description,
            expected_output="JSON object with analysis results",
            agent=node.runtime_agent,
        )
        crew = Crew(
            agents=[node.runtime_agent],
            tasks=[task],
            verbose=False,
        )

        result = crew.kickoff()
        raw_output = str(result.raw) if hasattr(result, "raw") else str(result)
        return _normalize_to_envelope(agent_id, raw_output)

    except Exception as exc:
        logger.warning("CrewAI dispatch failed for %s: %s", agent_id, exc)
        return AgentEnvelope.error_envelope(f"{agent_id} execution error: {str(exc)[:500]}")


def _dispatch_external_agent(
    agent_id: str,
    context: dict[str, Any],
) -> AgentEnvelope:
    """Dispatch external API agents (Gemini, ElevenLabs)."""
    try:
        if agent_id == "pipeline_classifier":
            return _run_pipeline_classifier(context)
        if agent_id in ("image_multimodal_processor",):
            return AgentEnvelope.warning_envelope(
                f"{agent_id}: vision processing deferred (no image inputs in context)"
            )
        if agent_id == "elevenlabs_narration":
            return _run_elevenlabs_narration(context)
        return AgentEnvelope.warning_envelope(f"External agent {agent_id} not implemented")
    except Exception as exc:
        return AgentEnvelope.error_envelope(f"{agent_id} external error: {str(exc)[:500]}")


def _dispatch_system_agent(
    agent_id: str,
    context: dict[str, Any],
) -> AgentEnvelope:
    """System-layer agents produce metadata without LLM calls."""
    if agent_id == "data_provenance_tracker":
        return AgentEnvelope(
            status="ok",
            summary="Provenance tracking recorded for all processed artifacts",
            confidence=1.0,
        )
    return AgentEnvelope.warning_envelope(f"System agent {agent_id} not implemented")


def _run_pipeline_classifier(context: dict[str, Any]) -> AgentEnvelope:
    """Use Gemini to classify track, then LIGHT_MODEL, then rule-based fallback."""
    track = context.get("track", "predictive")
    onboarding_path = context.get("onboarding_path", "")
    prompt = (
        f"Classify this business analysis request into one track.\n"
        f"Company context: {context.get('company_name', 'Unknown')}\n"
        f"User goal: {onboarding_path}\n"
        f"Files: {len(context.get('source_file_ids', []))} uploaded\n\n"
        f"Available tracks: predictive, automation, optimization, supply_chain\n\n"
        "Respond with ONLY a JSON object:\n"
        "{\n"
        '  "track": "<one of the four tracks>",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "skip_agents": ["<agent_id>", ...],\n'
        '  "recommended_agents": ["<agent_id>", ...]\n'
        "}\n"
        "skip_agents: pipeline agents that are clearly irrelevant for this track "
        "(use [] if unsure).\n"
        "recommended_agents: highest-value agents for this track (use [] if unsure).\n"
        "Valid agent_id examples: automation_strategy, trend_forecasting, "
        "sentiment_analysis, swot_analysis, conflict_detection, insight_generation, "
        "knowledge_graph_builder, public_data_scraper."
    )

    def _build_llm_envelope(raw: str, source: str) -> AgentEnvelope | None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        parsed = _finalize_classifier_result(parsed, onboarding_path)
        return AgentEnvelope(
            status="ok",
            summary=f"Track classified ({source}): {parsed.get('track', track)}",
            confidence=float(parsed.get("confidence", 0.8)),
            artifacts=[{"type": "classification", "source": source, "result": parsed}],
        )

    if settings.gemini_api_key_configured:
        try:
            from services.external_agent_clients import gemini_chat_completion
            raw = gemini_chat_completion(prompt, "You are a pipeline classification agent.")
            envelope = _build_llm_envelope(raw, "gemini")
            if envelope is not None:
                return envelope
            logger.warning("Gemini classifier returned non-JSON payload; trying LIGHT_MODEL fallback")
        except Exception as exc:
            logger.warning("Gemini classifier failed, trying LIGHT_MODEL fallback: %s", exc)

    # Backup path: run classification on the configured LIGHT_MODEL via Featherless.
    try:
        from services.external_agent_clients import llm_chat_completion

        raw = llm_chat_completion(
            model=settings.light_model,
            user_message=prompt,
            system_instruction="You are a pipeline classification agent.",
            max_tokens=450,
        )
        envelope = _build_llm_envelope(raw, "light_model_fallback")
        if envelope is not None:
            return envelope
        logger.warning("LIGHT_MODEL classifier fallback returned non-JSON payload; using rule fallback")
    except Exception as exc:
        logger.warning("LIGHT_MODEL classifier fallback failed, using rule fallback: %s", exc)

    # Rule-based fallback using onboarding_path
    resolved = resolve_track(onboarding_path)
    result = _finalize_classifier_result({"track": resolved.value, "confidence": 0.7}, onboarding_path)
    return AgentEnvelope(
        status="ok",
        summary=f"Track classified (rule-based fallback): {resolved.value}",
        confidence=0.7,
        artifacts=[{"type": "classification", "result": result}],
    )


def _run_elevenlabs_narration(context: dict[str, Any]) -> AgentEnvelope:
    """Generate insight podcast MP3: LLM-written script from full analysis, then ElevenLabs TTS."""
    summary_text = _resolve_executive_summary_text(context)
    if not summary_text:
        return AgentEnvelope.warning_envelope("No executive summary available for narration")

    if not settings.elevenlabs_api_key_configured:
        return AgentEnvelope.warning_envelope("ElevenLabs API key not configured")

    script_llm = _generate_podcast_script_via_llm(context)
    if script_llm.strip():
        script = script_llm
        script_source = "llm_podcast"
    else:
        script = (
            "Welcome to your Datalyze insight briefing. "
            "Here is the executive summary for this analysis. "
            + summary_text
        )
        script_source = "fallback_exec_summary"
        logger.info("Using fallback narration script (podcast LLM unavailable or too short)")

    tts_payload = script[:5000]

    try:
        from services.external_agent_clients import elevenlabs_synthesize_mp3

        audio_bytes = elevenlabs_synthesize_mp3(tts_payload)
        run_dir = context.get("_run_dir")
        if run_dir:
            base = Path(run_dir) / "artifacts"
            audio_path = base / "narration.mp3"
            audio_path.write_bytes(audio_bytes)
            rel = str(audio_path.relative_to(base))
            return AgentEnvelope(
                status="ok",
                summary="Insight podcast audio generated (LLM script + ElevenLabs)",
                confidence=1.0,
                artifacts=[
                    {
                        "type": "audio",
                        "path": rel,
                        "format": "mp3",
                        "narration_text": tts_payload[:2000],
                        "status": "ok",
                        "script_source": script_source,
                        "approx_word_count": _word_count_spoken(tts_payload),
                    },
                ],
            )
        return AgentEnvelope(
            status="ok",
            summary="Insight podcast audio generated (in memory)",
            confidence=1.0,
            artifacts=[
                {
                    "type": "audio",
                    "format": "mp3",
                    "narration_text": tts_payload[:2000],
                    "status": "ok",
                },
            ],
        )
    except Exception as exc:
        return AgentEnvelope.error_envelope(f"Narration error: {str(exc)[:500]}")


def _build_task_prompt(
    agent_id: str,
    spec: Any,
    context: dict[str, Any],
) -> str:
    """Build a context-aware task prompt for a CrewAI agent."""
    company = context.get("company_name", "Unknown Company")
    track = context.get("track", "predictive")
    file_count = len(context.get("source_file_ids", []))
    prior_outputs = context.get("prior_outputs", {})

    # Build a summary of what prior agents produced
    prior_summary = ""
    if prior_outputs:
        summaries = [f"- {aid}: {out.get('summary', 'done')}" for aid, out in prior_outputs.items()]
        prior_summary = "\nPrior agent results:\n" + "\n".join(summaries[-10:])

    retry_hint = context.get("_retry_hint", "")
    retry_section = f"\n\nIMPORTANT: {retry_hint}" if retry_hint else ""

    brain = context.get("orchestrator_brain")
    brain_section = ""
    if isinstance(brain, dict):
        brief = (brain.get("orchestrator_brief") or "").strip()
        if brief:
            brain_section = f"\n--- Orchestrator context (heavy model) ---\n{brief}\n"
        ag = brain.get("per_agent_guidance") or {}
        if isinstance(ag, dict) and spec.id in ag:
            g = str(ag.get(spec.id, "")).strip()
            if g:
                brain_section += f"\n--- Guidance for this agent ---\n{g}\n"

    cr = context.get("classifier_routing") or {}
    routing_section = ""
    if isinstance(cr, dict):
        rec = cr.get("recommended_agents") or []
        sk = cr.get("skip_agents") or []
        if rec or sk:
            routing_section = (
                "\n--- Classifier routing ---\n"
                f"Recommended emphasis: {rec}\n"
                f"Skipped for this run: {sk}\n"
            )

    return (
        f"You are the {spec.name} for the Datalyze platform.\n"
        f"Role: {spec.responsibilities}\n"
        f"Company: {company}\n"
        f"Analysis track: {track}\n"
        f"Input files: {file_count}\n"
        f"{routing_section}"
        f"{brain_section}"
        f"{prior_summary}\n\n"
        f"Your input: {spec.input_description}\n"
        f"Your expected output: {spec.output_description}\n\n"
        f"Produce a concise JSON response with your analysis results. "
        f"Keep output under 500 tokens. Focus on actionable findings."
        f"{retry_section}"
    )


def _normalize_to_envelope(agent_id: str, raw_output: str) -> AgentEnvelope:
    """Normalize raw agent output to AgentEnvelope.

    Integration seam: Shivam's per-agent JSON schemas will be enforced
    here once merged. Currently wraps any output into the envelope.
    """
    # Try parsing as JSON first
    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, dict):
            # If it already matches envelope shape, use it directly
            if "status" in parsed and "summary" in parsed:
                return AgentEnvelope.from_dict(parsed)
            # Otherwise wrap the parsed content
            return AgentEnvelope(
                status="ok",
                summary=str(parsed.get("summary", f"{agent_id} completed"))[:500],
                artifacts=[{"type": "agent_output", "data": parsed}],
                confidence=float(parsed.get("confidence", 0.6)),
            )
    except (json.JSONDecodeError, ValueError):
        pass

    # Wrap raw text output
    return AgentEnvelope(
        status="ok",
        summary=raw_output[:500] if raw_output else f"{agent_id} completed",
        confidence=0.5,
    )


class OrchestratorEngine:
    """Production orchestrator engine that drives the full pipeline lifecycle."""

    def __init__(
        self,
        run_id: int,
        run_slug: str,
        company_id: int,
        company_name: str,
        user_id: int,
        user_name: str,
        source_file_ids: list[int],
        source_files_meta: list[dict[str, Any]] | None = None,
        onboarding_path: str | None = None,
        public_scrape_enabled: bool = False,
        skip_input_dedup: bool = False,
    ):
        self.run_id = run_id
        self.run_slug = run_slug
        self.company_id = company_id
        self.company_name = company_name
        self.user_id = user_id
        self.user_name = user_name
        self.source_file_ids = source_file_ids
        self.source_files_meta = source_files_meta or []
        self.public_scrape_enabled = public_scrape_enabled
        self.onboarding_path = onboarding_path or ""
        self.skip_input_dedup = skip_input_dedup

        self.track_id = resolve_track(onboarding_path)
        self.profile = get_track_profile(self.track_id)
        self.dep_map = _build_dependency_map()

        self.memory = MemoryState()
        self.run_dir: Path | None = None
        self.start_time: float = 0.0
        self.step_counter: int = 0
        self.context: dict[str, Any] = {}
        self.prior_outputs: dict[str, dict[str, Any]] = {}
        self._input_hash: str = ""
        self._finalized_cancel: bool = False

    def _run_log(
        self,
        stage: str,
        agent: str,
        action: str,
        detail: str,
        status: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Persist pipeline log row. Per-line ElevenLabs TTS is disabled for MVP (podcast playbook only)."""
        d = (detail or "")[:2000]
        db_insert_run_log(self.run_id, stage, agent, action, d, status, meta)

    def _abort_if_cancelled(self) -> bool:
        """If user requested stop, finalize as cancelled and return True."""
        if self._finalized_cancel:
            return True
        if not is_cancel_requested(self.run_slug):
            return False
        self._finalize_cancelled()
        return True

    def _finalize_cancelled(self) -> None:
        """Mark run cancelled in DB and artifacts (cooperative stop)."""
        if self._finalized_cancel:
            return
        self._finalized_cancel = True
        clear_cancel_request(self.run_slug)
        self.memory.state = "cancelled"
        self.memory.done = True
        self.memory.add_event("run_cancelled", "orchestrator", "Stopped by user request")

        summary = (
            f"Analysis stopped by user. "
            f"Partial progress: {len(self.memory.completed)} agent(s) completed."
        )
        pipeline_log = [
            f"[{e['timestamp']}] [{e['agent']}] {e['type']}: {e.get('detail', '')}"
            for e in self.memory.events
        ]
        agent_activity: list[dict[str, Any]] = []
        for agent_id in self.memory.completed:
            agent_activity.append({
                "agent_id": agent_id,
                "agent_name": agent_id.replace("_", " ").title(),
                "status": "completed",
                "message": self.prior_outputs.get(agent_id, {}).get("summary", "Completed"),
            })
        for agent_id in self.memory.skipped:
            agent_activity.append({
                "agent_id": agent_id,
                "agent_name": agent_id.replace("_", " ").title(),
                "status": "skipped",
                "message": "Skipped",
            })

        replay_payload: dict[str, Any] = {
            "cancelled": True,
            "agent_activity": agent_activity,
            "pipeline_log": pipeline_log[-100:],
        }
        if self.run_dir:
            write_memory(self.run_dir, self.memory)
            replay_payload["run_dir"] = run_dir_relative(self.run_dir)
            final_report = {
                "run_slug": self.run_slug,
                "track": self.track_id.value,
                "status": "cancelled",
                "summary": summary,
                "cancelled": True,
                "finalized_at": datetime.now(UTC).isoformat(),
            }
            write_final_report(self.run_dir, final_report)
            replay_payload["final_report"] = final_report

        db_update_run_status(
            self.run_id,
            status="cancelled",
            summary=summary,
            pipeline_log=pipeline_log or [f"[{self.run_slug}] Analysis stopped by user."],
            agent_activity=agent_activity,
            replay_payload=replay_payload,
            run_dir_path=run_dir_relative(self.run_dir) if self.run_dir else None,
        )
        self._run_log(
            "system", "orchestrator", "run_cancelled",
            "Run stopped by user (cooperative cancellation).", "warning",
        )
        logger.info("Run %s cancelled by user", self.run_slug)

    def execute(self) -> None:
        """Run the full pipeline. Called from background thread."""
        self.start_time = time.time()
        now = datetime.now(UTC)

        try:
            if is_cancel_requested(self.run_slug):
                clear_cancel_request(self.run_slug)
                db_update_run_status(
                    self.run_id,
                    status="cancelled",
                    summary="Analysis stopped by user before execution started.",
                )
                self._run_log(
                    "system", "orchestrator", "run_cancelled",
                    "Cancelled before run directory was created.", "warning",
                )
                return

            # Create run directory
            self.run_dir = create_run_directory(
                track=self.track_id.value,
                company_name=self.company_name,
                user_name=self.user_name,
                run_slug=self.run_slug,
                timestamp=now,
            )

            self._init_context()
            self._write_initial_artifacts(now)

            # 1.4 — Deduplication: same inputs within 24h → redirect; older match → note in context
            self._input_hash = self._compute_input_hash()
            prior_match = None
            if not self.skip_input_dedup:
                prior_match = db_find_latest_matching_completed_run(
                    self.company_id, self._input_hash, self.run_id,
                )
            if prior_match:
                started = prior_match["started_at"]
                if started is not None:
                    if getattr(started, "tzinfo", None) is None:
                        started = started.replace(tzinfo=UTC)
                    else:
                        started = started.astimezone(UTC)
                    age_sec = (datetime.now(UTC) - started).total_seconds()
                    if age_sec < 24 * 3600:
                        dup_slug = prior_match["run_slug"]
                        db_update_run_status(
                            self.run_id,
                            status="duplicate",
                            summary=(
                                "A similar analysis was recently completed. "
                                "Redirecting to the most recent matching analysis."
                            ),
                            replay_payload={
                                "redirect_to_slug": dup_slug,
                                "reason": "duplicate_input",
                            },
                            input_hash=self._input_hash,
                        )
                        self._run_log(
                            "system", "orchestrator", "duplicate_detected",
                            f"Duplicate of run {dup_slug}", "info",
                        )
                        return
                self.context["previous_matching_analysis_slug"] = prior_match["run_slug"]
                self.memory.warnings.append(
                    f"Prior analysis with the same inputs exists (run {prior_match['run_slug']}); "
                    "proceeding with a fresh run."
                )

            # Mark run as running in DB
            db_update_run_status(
                self.run_id,
                status="running",
                track=self.track_id.value,
                config_json=self._build_config_json(),
                run_dir_path=run_dir_relative(self.run_dir),
                input_hash=self._input_hash,
            )

            self._run_log(
                "system", "orchestrator", "run_started",
                f"Track: {self.track_id.value}, Files: {len(self.source_file_ids)}",
                "start",
            )

            if self._abort_if_cancelled():
                return

            # Execute each stage
            for stage_config in self.profile.stages:
                if self._is_budget_exceeded():
                    self.memory.warnings.append("Time budget exceeded, finalizing early")
                    break

                if self._abort_if_cancelled():
                    return

                self._execute_stage(stage_config)

                if stage_config.stage_id == StageID.CLASSIFY:
                    self._apply_heavy_orchestration_brain()

                if self._abort_if_cancelled():
                    return

            if self._finalized_cancel:
                return

            # Finalize
            self._finalize()

        except Exception as exc:
            if self._finalized_cancel:
                return
            logger.error("Orchestrator fatal error: %s\n%s", exc, traceback.format_exc())
            self.memory.state = "failed"
            self.memory.add_event("fatal_error", "orchestrator", str(exc)[:1000])
            if self.run_dir:
                write_memory(self.run_dir, self.memory)
            db_update_run_status(
                self.run_id,
                status="failed",
                summary=f"Pipeline failed: {str(exc)[:500]}",
            )
            self._run_log(
                "system", "orchestrator", "fatal_error",
                str(exc)[:1000], "error",
            )

    def _init_context(self) -> None:
        """Build initial execution context."""
        self.context = {
            "track": self.track_id.value,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "source_file_ids": self.source_file_ids,
            "source_files_meta": self.source_files_meta,
            "public_scrape_enabled": self.public_scrape_enabled,
            "onboarding_path": self.onboarding_path,
            "_run_dir": str(self.run_dir),
            "prior_outputs": self.prior_outputs,
            "orchestrator_brain": {},
            "classifier_routing": {},
        }

        # Build list of all agents across all stages
        all_agents = self.profile.all_agent_ids()
        self.memory.pending = list(all_agents)

    def _write_initial_artifacts(self, now: datetime) -> None:
        """Write initial filesystem artifacts."""
        assert self.run_dir is not None

        manifest = RunManifest(
            run_slug=self.run_slug,
            track=self.track_id.value,
            company_id=self.company_id,
            company_name=self.company_name,
            user_id=self.user_id,
            source_file_ids=self.source_file_ids,
            public_scrape_enabled=self.public_scrape_enabled,
            parallel_enabled=settings.orch_enable_parallel_branches,
            adaptive_policy_enabled=settings.orch_enable_adaptive_policy,
            stage_gates_enabled=settings.orch_enable_stage_gates,
            max_run_seconds=settings.orch_max_run_seconds,
            created_at=now.isoformat(),
            model_config={
                "heavy_model": settings.heavy_model,
                "heavy_alt_model": settings.heavy_alt_model,
                "light_model": settings.light_model,
                "llm_provider": settings.llm_provider,
                "orch_heavy_brain_enabled": str(settings.orch_heavy_brain_enabled),
            },
        )
        write_manifest(self.run_dir, manifest)
        write_memory(self.run_dir, self.memory)
        write_context_index(self.run_dir, {
            "run_slug": self.run_slug,
            "track": self.track_id.value,
            "stages": [s.stage_id.value for s in self.profile.stages],
            "created_at": now.isoformat(),
        })
        write_input_metadata(self.run_dir, {
            "source_file_ids": self.source_file_ids,
            "source_files": self.source_files_meta,
            "public_scrape_enabled": self.public_scrape_enabled,
        })
        update_artifacts_index(self.run_dir, [])

    def _apply_heavy_orchestration_brain(self) -> None:
        """After Gemini classification, call ``HEAVY_MODEL`` (``settings.heavy_model`` / .env) only."""
        if not settings.orch_heavy_brain_enabled:
            return
        if "pipeline_classifier" not in self.prior_outputs:
            return
        arts = self.prior_outputs.get("pipeline_classifier", {}).get("artifacts", [])
        classifier_result = _artifact_primary_payload(arts)
        if not classifier_result:
            return
        brain = run_heavy_orchestration_brain(
            track=self.track_id.value,
            company_name=self.company_name,
            onboarding_path=self.onboarding_path,
            source_files_meta=self.source_files_meta,
            classifier_result=classifier_result,
            focus_agents=list(self.profile.focus_agents),
        )
        self.context["orchestrator_brain"] = brain
        detail = f"heavy_model={brain.get('heavy_model')}; skips={brain.get('skip_agents')}"
        brief = (brain.get("orchestrator_brief") or "").strip()
        if brief:
            detail += f"; brief_chars={len(brief)}"
        self.memory.add_event("orchestrator_brain", "orchestrator", detail[:500])
        if self.run_dir:
            write_memory(self.run_dir, self.memory)
        self._run_log(
            "classify", "orchestrator", "heavy_brain",
            detail[:2000], "info",
        )

    def _execute_stage(self, stage_config: Any) -> None:
        """Execute all agents in a stage respecting DAG and policies."""
        if self._abort_if_cancelled():
            return

        stage_id = stage_config.stage_id
        self.memory.current_stage = stage_id.value
        self.memory.add_event("stage_started", "orchestrator", stage_id.value)
        write_memory(self.run_dir, self.memory)

        self._run_log(
            stage_id.value, "orchestrator", "stage_started",
            f"Starting stage: {stage_id.value}", "start",
        )

        all_stage_agents = stage_config.agents + stage_config.optional_agents
        # Filter to agents that actually exist in registry
        registry = get_registry()
        valid_agents = [a for a in all_stage_agents if a in registry.specs_by_id]

        # Skip file processors if no files uploaded and agent is a processor
        if not self.source_file_ids:
            processor_agents = {
                "pdf_processor", "csv_processor", "excel_processor",
                "json_processor", "image_multimodal_processor", "plain_text_processor",
            }
            skippable = [a for a in valid_agents if a in processor_agents]
            for a in skippable:
                self.memory.skipped.append(a)
                if a in self.memory.pending:
                    self.memory.pending.remove(a)
                self.memory.add_event("agent_skipped", a, "No files to process")

        # 1.1a — Classifier + heavy-brain merged skip list + context routing
        classifier_artifacts = self.prior_outputs.get("pipeline_classifier", {}).get("artifacts", [])
        classifier_result = _artifact_primary_payload(classifier_artifacts)
        skip_list: list[str] = []
        if classifier_result:
            brain_skips: list[str] = []
            ob = self.context.get("orchestrator_brain")
            if isinstance(ob, dict):
                brain_skips = [x for x in (ob.get("skip_agents") or []) if isinstance(x, str)]
            merged_skip = merge_skip_agent_lists(
                [x for x in (classifier_result.get("skip_agents") or []) if isinstance(x, str)],
                brain_skips,
            )
            self.context["classifier_routing"] = {
                "skip_agents": merged_skip,
                "recommended_agents": [
                    x for x in (classifier_result.get("recommended_agents") or []) if isinstance(x, str)
                ],
            }
            self.context["prior_outputs"] = self.prior_outputs
            skip_list = merged_skip
        if skip_list:
            for a in valid_agents:
                if (a in skip_list
                        and a not in self.memory.completed
                        and a not in self.memory.skipped):
                    self.memory.skipped.append(a)
                    if a in self.memory.pending:
                        self.memory.pending.remove(a)
                    self.memory.add_event("agent_skipped", a, "Classifier recommended skip")

        # 1.1b — File-type classifier processor routing (file_routing list and/or file_routing_map)
        if "file_type_classifier" in self.prior_outputs:
            ftc_artifacts = self.prior_outputs["file_type_classifier"].get("artifacts", [])
            ftc_result = _artifact_primary_payload(ftc_artifacts)
            needed_processors = _needed_processors_from_ftc_result(ftc_result)
            if needed_processors:
                all_file_processors = {
                    "pdf_processor", "csv_processor", "excel_processor",
                    "json_processor", "plain_text_processor", "image_multimodal_processor",
                }
                for a in valid_agents:
                    if (a in all_file_processors
                            and a not in needed_processors
                            and a not in self.memory.completed
                            and a not in self.memory.skipped):
                        self.memory.skipped.append(a)
                        if a in self.memory.pending:
                            self.memory.pending.remove(a)
                        self.memory.add_event("agent_skipped", a, "No matching file type for this processor")

        # 1.3 — Wrap-up phase: skip optional agents when approaching time limit
        budget = check_time_budget(self.start_time)
        self.memory.timing_budget = budget
        if budget.get("in_wrap_up_phase"):
            if not any("wrap-up phase" in w for w in self.memory.warnings):
                self.memory.warnings.append("Entered wrap-up phase — finalizing with available results")
            for a in stage_config.optional_agents:
                if (a not in self.memory.completed
                        and a not in self.memory.failed
                        and a not in self.memory.skipped):
                    self.memory.skipped.append(a)
                    if a in self.memory.pending:
                        self.memory.pending.remove(a)
                    self.memory.add_event("agent_skipped", a, "Skipped — wrap-up phase active")

        # Orchestrator loop for this stage
        max_stage_iterations = len(valid_agents) * 3  # safety cap
        iteration = 0

        while iteration < max_stage_iterations:
            iteration += 1

            if self._abort_if_cancelled():
                return

            if self._is_budget_exceeded():
                break

            next_agents = pick_next_agents(
                stage_agents=valid_agents,
                completed=self.memory.completed,
                failed=self.memory.failed,
                skipped=self.memory.skipped,
                agent_dependencies=self.dep_map,
                parallel_enabled=settings.orch_enable_parallel_branches,
                adaptive_enabled=settings.orch_enable_adaptive_policy,
                focus_agents=self.profile.focus_agents,
                retries=self.memory.retries,
            )
            self.memory.next_candidates = list(next_agents)
            write_memory(self.run_dir, self.memory)

            if not next_agents:
                break

            if settings.orch_enable_parallel_branches and len(next_agents) > 1:
                self._dispatch_parallel(next_agents)
            else:
                for agent_id in next_agents:
                    if self._abort_if_cancelled():
                        return
                    self._dispatch_single(agent_id, stage_id.value)

        # Stage gate
        if stage_config.quality_gate and settings.orch_enable_stage_gates:
            gate_result = evaluate_stage_gate(
                stage_id,
                self.memory,
                stage_config.agents,
                stage_config.optional_agents,
                prior_outputs=self.prior_outputs,
            )
            if self.run_dir:
                write_quality_gate(self.run_dir, gate_result)

            if not gate_result.passed:
                self.memory.warnings.extend(gate_result.issues)
                self._run_log(
                    stage_id.value, "orchestrator", "gate_failed",
                    "; ".join(gate_result.issues), "warning",
                )

        self._run_log(
            stage_id.value, "orchestrator", "stage_completed",
            f"Stage {stage_id.value} done", "success",
        )

    def _dispatch_single(self, agent_id: str, stage: str) -> None:
        """Dispatch a single agent with retry support."""
        if self._abort_if_cancelled():
            return

        self.step_counter += 1
        step = self.step_counter

        self.memory.current_agent = agent_id
        self.memory.step_count = step
        self.memory.add_event("agent_started", agent_id, f"Step {step}")
        if agent_id in self.memory.pending:
            self.memory.pending.remove(agent_id)
        write_memory(self.run_dir, self.memory)

        self._run_log(
            stage, agent_id, "dispatch",
            f"Dispatching {agent_id} (step {step})", "start",
        )

        # Record decision
        why = f"DAG ready, track={self.track_id.value}"
        ob = self.context.get("orchestrator_brain")
        if settings.orch_heavy_brain_enabled and isinstance(ob, dict):
            guides = ob.get("per_agent_guidance") or {}
            if isinstance(guides, dict) and agent_id in guides:
                g = str(guides.get(agent_id, "")).strip()
                if g:
                    why = f"Heavy-orchestrated: {g[:280]}"
        decision = DecisionRecord(
            timestamp=datetime.now(UTC).isoformat(),
            step=step,
            stage=stage,
            agent_id=agent_id,
            why_this_agent=why,
            alternatives_considered=[],
            policy_mode="adaptive" if settings.orch_enable_adaptive_policy else "deterministic",
            confidence=0.0,
            outcome="dispatched",
        )
        decision.alternatives_considered = [
            c for c in self.memory.next_candidates if c != agent_id
        ]

        # Update context with prior outputs
        self.context["prior_outputs"] = self.prior_outputs

        # Dispatch
        envelope = _dispatch_agent(agent_id, self.context, self.run_dir)

        # Retry logic
        if envelope.status == "error":
            retry = evaluate_retry(agent_id, envelope, self.memory)
            while retry.should_retry:
                self.memory.retries[agent_id] = retry.attempt
                self.memory.add_event("agent_retry", agent_id, retry.reason)
                write_memory(self.run_dir, self.memory)

                self._run_log(
                    stage, agent_id, "retry",
                    f"Retry attempt {retry.attempt}: {retry.reason}", "warning",
                )

                if retry.delay_seconds > 0:
                    time.sleep(retry.delay_seconds)

                envelope = _dispatch_agent(agent_id, self.context, self.run_dir)
                if envelope.status != "error":
                    break
                retry = evaluate_retry(agent_id, envelope, self.memory)

        # 1.5 — Guardrails: retry on empty/minimal output
        if envelope.status != "error" and _is_minimal_output(envelope):
            self.memory.add_event("agent_retry", agent_id, "Minimal output — retrying with enhanced context")
            enhanced_ctx = dict(self.context)
            enhanced_ctx["prior_outputs"] = self.prior_outputs
            enhanced_ctx["_retry_hint"] = (
                "Your previous response was too brief. Provide a detailed, substantive analysis "
                "with specific findings, metrics, and actionable recommendations."
            )
            retry_envelope = _dispatch_agent(agent_id, enhanced_ctx, self.run_dir)
            if not _is_minimal_output(retry_envelope):
                envelope = retry_envelope
            else:
                self.memory.warnings.append(f"Agent {agent_id} produced minimal output after retry")

        # 1.5 — Guardrails: retry on low confidence (once, only if not already retried)
        elif (envelope.status != "error"
              and envelope.confidence < 0.4
              and self.memory.retries.get(agent_id, 0) == 0):
            self.memory.add_event(
                "agent_retry", agent_id,
                f"Low confidence ({envelope.confidence:.2f}) — retrying with additional context",
            )
            enhanced_ctx = dict(self.context)
            enhanced_ctx["prior_outputs"] = self.prior_outputs
            enhanced_ctx["_retry_hint"] = (
                "Your previous response had low confidence. Provide more specific, "
                "data-driven analysis with concrete figures and evidence."
            )
            retry_envelope = _dispatch_agent(agent_id, enhanced_ctx, self.run_dir)
            if retry_envelope.status != "error":
                envelope = retry_envelope
            else:
                self.memory.warnings.append(
                    f"Agent {agent_id} confidence {envelope.confidence:.2f} below threshold"
                )

        # Record outcome
        if envelope.status == "error":
            decision.outcome = "failed"
            self.memory.failed.append(agent_id)
            self.memory.add_event("agent_failed", agent_id, envelope.summary)
            self._run_log(
                stage, agent_id, "failed",
                envelope.summary[:500], "error",
            )
        else:
            decision.outcome = "completed"
            decision.confidence = envelope.confidence
            self.memory.completed.append(agent_id)
            self.prior_outputs[agent_id] = envelope.to_dict()
            self.memory.add_event("agent_completed", agent_id, envelope.summary[:200])
            self._run_log(
                stage, agent_id, "completed",
                envelope.summary[:500], "success",
                {"confidence": envelope.confidence},
            )

            # Persist artifacts
            if envelope.artifacts:
                stamped_artifacts = [
                    {**a, "producer": agent_id, "timestamp": datetime.now(UTC).isoformat()}
                    for a in envelope.artifacts
                ]
                update_artifacts_index(self.run_dir, stamped_artifacts)
                db_insert_artifacts(self.run_id, agent_id, stamped_artifacts)

        append_decision(self.run_dir, decision)
        write_agent_output(self.run_dir, agent_id, step, envelope)
        write_memory(self.run_dir, self.memory)

    def _dispatch_parallel(self, agent_ids: list[str]) -> None:
        """Dispatch multiple agents in parallel using thread pool."""
        if self._abort_if_cancelled():
            return

        stage = self.memory.current_stage
        futures = {}

        with ThreadPoolExecutor(max_workers=min(len(agent_ids), 4)) as executor:
            for agent_id in agent_ids:
                self.step_counter += 1
                step = self.step_counter
                self.memory.add_event("agent_started", agent_id, f"Step {step} (parallel)")
                if agent_id in self.memory.pending:
                    self.memory.pending.remove(agent_id)

                self._run_log(
                    stage, agent_id, "dispatch",
                    f"Dispatching {agent_id} (step {step})", "start",
                )

                ctx = dict(self.context)
                ctx["prior_outputs"] = dict(self.prior_outputs)
                future = executor.submit(_dispatch_agent, agent_id, ctx, self.run_dir)
                futures[future] = (agent_id, step)

            write_memory(self.run_dir, self.memory)

            for future in as_completed(futures):
                if self._abort_if_cancelled():
                    return
                agent_id, step = futures[future]
                try:
                    envelope = future.result(timeout=settings.orchestrator_timeout_seconds)
                except Exception as exc:
                    envelope = AgentEnvelope.error_envelope(f"Parallel dispatch error: {str(exc)[:500]}")

                if envelope.status == "error":
                    self.memory.failed.append(agent_id)
                    self.memory.add_event("agent_failed", agent_id, envelope.summary)
                    self._run_log(
                        stage, agent_id, "failed",
                        envelope.summary[:500], "error",
                    )
                else:
                    self.memory.completed.append(agent_id)
                    self.prior_outputs[agent_id] = envelope.to_dict()
                    self.memory.add_event("agent_completed", agent_id, envelope.summary[:200])
                    self._run_log(
                        stage, agent_id, "completed",
                        envelope.summary[:500], "success",
                    )

                write_agent_output(self.run_dir, agent_id, step, envelope)
                append_decision(self.run_dir, DecisionRecord(
                    timestamp=datetime.now(UTC).isoformat(),
                    step=step,
                    stage=stage,
                    agent_id=agent_id,
                    why_this_agent="parallel dispatch",
                    alternatives_considered=[],
                    policy_mode="adaptive" if settings.orch_enable_adaptive_policy else "deterministic",
                    confidence=envelope.confidence,
                    outcome="completed" if envelope.status != "error" else "failed",
                ))
                if envelope.artifacts:
                    stamped_artifacts = [
                        {**a, "producer": agent_id, "timestamp": datetime.now(UTC).isoformat()}
                        for a in envelope.artifacts
                    ]
                    update_artifacts_index(self.run_dir, stamped_artifacts)
                    db_insert_artifacts(self.run_id, agent_id, stamped_artifacts)

        write_memory(self.run_dir, self.memory)

    def _is_budget_exceeded(self) -> bool:
        budget = check_time_budget(self.start_time)
        self.memory.timing_budget = budget
        return budget["budget_exceeded"]

    def _finalize(self) -> None:
        """Finalize the run: write final report, update DB projection."""
        self.memory.timing_budget = check_time_budget(self.start_time)
        final_status = classify_completion(self.memory)
        self.memory.state = final_status
        self.memory.done = True

        if final_status == "completed_with_warnings":
            self.memory.fix_suggestions = generate_fix_suggestions(self.memory)

        self.memory.add_event("run_completed", "orchestrator", final_status)
        write_memory(self.run_dir, self.memory)

        # Build pipeline log (list of strings for backward compat)
        pipeline_log = [
            f"[{e['timestamp']}] [{e['agent']}] {e['type']}: {e.get('detail', '')}"
            for e in self.memory.events
        ]

        # Build agent activity (list of dicts for backward compat)
        agent_activity = []
        for agent_id in self.memory.completed:
            agent_activity.append({
                "agent_id": agent_id,
                "agent_name": agent_id.replace("_", " ").title(),
                "status": "completed",
                "message": self.prior_outputs.get(agent_id, {}).get("summary", "Completed"),
            })
        for agent_id in self.memory.failed:
            agent_activity.append({
                "agent_id": agent_id,
                "agent_name": agent_id.replace("_", " ").title(),
                "status": "failed",
                "message": f"Failed after {self.memory.retries.get(agent_id, 0)} retries",
            })
        for agent_id in self.memory.skipped:
            agent_activity.append({
                "agent_id": agent_id,
                "agent_name": agent_id.replace("_", " ").title(),
                "status": "skipped",
                "message": "Skipped (not applicable for this run)",
            })

        # Build summary
        summary = (
            f"Track: {self.track_id.value} | "
            f"Status: {final_status} | "
            f"Completed: {len(self.memory.completed)}/{len(self.memory.completed) + len(self.memory.failed) + len(self.memory.skipped)} agents | "
            f"Duration: {self.memory.timing_budget.get('elapsed_seconds', 0)}s"
        )
        if self.memory.warnings:
            summary += f" | Warnings: {len(self.memory.warnings)}"

        structured = _collect_structured_outputs(self.prior_outputs)
        from services.agents.output_evaluator import build_visualization_plan as _build_viz

        visualization_plan = _build_viz(structured)
        agent_results_payload = {**structured, "output_evaluator": visualization_plan}

        # Final report
        final_report = {
            "run_slug": self.run_slug,
            "track": self.track_id.value,
            "status": final_status,
            "summary": summary,
            "completed_agents": self.memory.completed,
            "failed_agents": self.memory.failed,
            "skipped_agents": self.memory.skipped,
            "warnings": self.memory.warnings,
            "fix_suggestions": self.memory.fix_suggestions,
            "timing": self.memory.timing_budget,
            "agent_results": agent_results_payload,
            "visualization_plan": visualization_plan,
            "agent_summaries": {
                aid: out.get("summary", "") for aid, out in self.prior_outputs.items()
            },
            "finalized_at": datetime.now(UTC).isoformat(),
        }
        write_final_report(self.run_dir, final_report)

        # Build replay payload for DB
        replay_payload = {
            "final_report": final_report,
            "agent_activity": agent_activity,
            "pipeline_log": pipeline_log[-100:],  # cap for DB size
            "run_dir": run_dir_relative(self.run_dir),
            "agent_results": agent_results_payload,
            "visualization_plan": visualization_plan,
        }

        # Update DB
        db_update_run_status(
            self.run_id,
            status=final_status,
            summary=summary,
            pipeline_log=pipeline_log,
            agent_activity=agent_activity,
            replay_payload=replay_payload,
            run_dir_path=run_dir_relative(self.run_dir),
        )

        if final_status in ("completed", "completed_with_warnings"):
            try:
                db_capture_demo_replay(
                    self.company_id,
                    self.run_id,
                    self.track_id.value,
                    replay_payload,
                )
            except Exception:
                logger.warning("demo_replay capture failed", exc_info=True)

        self._run_log(
            "system", "orchestrator", "finalized",
            summary, "success",
        )

        logger.info("Run %s finalized: %s", self.run_slug, final_status)

    def _build_config_json(self) -> dict:
        return {
            "track": self.track_id.value,
            "parallel_enabled": settings.orch_enable_parallel_branches,
            "adaptive_policy_enabled": settings.orch_enable_adaptive_policy,
            "stage_gates_enabled": settings.orch_enable_stage_gates,
            "max_run_seconds": settings.orch_max_run_seconds,
            "orch_heavy_brain_enabled": settings.orch_heavy_brain_enabled,
        }

    def _compute_input_hash(self) -> str:
        """SHA-256 of (company_id, sorted file IDs, track, onboarding_path) for dedup."""
        raw = (
            f"{self.company_id}:"
            f"{sorted(self.source_file_ids)}:"
            f"{self.track_id.value}:"
            f"{self.onboarding_path}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()
