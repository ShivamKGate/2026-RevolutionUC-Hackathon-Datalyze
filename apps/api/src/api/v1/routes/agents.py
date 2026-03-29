import json
import re

from fastapi import APIRouter, HTTPException

from core.config import settings
from core.ollama_models import HARDWARE_SUMMARY, MODELS, pull_commands
from schemas.agent_boot import AgentBootStatusResponse
from schemas.agents import (
    AgentHealthCheckItem,
    AgentHealthCheckResponse,
    AgentMVPRequest,
    AgentMVPResponse,
    ElevenLabsAgentVerifyRequest,
    ElevenLabsAgentVerifyResponse,
    GeminiAgentVerifyRequest,
    GeminiAgentVerifyResponse,
)
from schemas.ollama_catalog import OllamaCatalogResponse
from services.agent_registry import boot_registry, get_registry
from services.agents.contracts import AGENT_CONTRACTS, get_contract
from services.agents.normalizer import normalize_agent_output, validate_envelope
from services.crew_mvp import initialize_only_mvp, kickoff_mvp
from services.crew_specialized import initialize_specialized, kickoff_specialized
from services.external_agent_clients import (
    gemini_or_light_chat_completion_pair,
    elevenlabs_synthesize_mp3,
    llm_chat_completion,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/boot-status", response_model=AgentBootStatusResponse)
def agent_boot_status() -> AgentBootStatusResponse:
    registry = get_registry()
    if not registry.nodes:
        snapshot = boot_registry()
    else:
        snapshot = registry.snapshot()
    return AgentBootStatusResponse.model_validate(snapshot)


@router.post(
    "/verify/pipeline-classifier",
    response_model=GeminiAgentVerifyResponse,
    summary="Chat check for Pipeline Classifier (Gemini with light-model fallback)",
)
def verify_pipeline_classifier_gemini(
    payload: GeminiAgentVerifyRequest,
) -> GeminiAgentVerifyResponse:
    try:
        reply, src = gemini_or_light_chat_completion_pair(
            payload.message,
            system_instruction=(
                "You are the Datalyze pipeline classifier agent. "
                "Keep answers concise unless the user asks for detail."
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    model_used = settings.gemini_model if src == "gemini" else settings.light_model
    return GeminiAgentVerifyResponse(
        agent_id="pipeline_classifier",
        agent_name="Pipeline Classifier Agent",
        model=model_used,
        reply=reply,
    )


@router.post(
    "/verify/elevenlabs-narration",
    response_model=ElevenLabsAgentVerifyResponse,
    summary="TTS check for ElevenLabs Narration agent",
)
def verify_elevenlabs_narration(
    payload: ElevenLabsAgentVerifyRequest,
) -> ElevenLabsAgentVerifyResponse:
    if not settings.elevenlabs_api_key_configured:
        raise HTTPException(
            status_code=503,
            detail="ELEVENLABS_API_KEY is not set in apps/api/.env",
        )
    try:
        audio = elevenlabs_synthesize_mp3(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if len(audio) < 100:
        raise HTTPException(
            status_code=502,
            detail="ElevenLabs returned an unexpectedly small response body",
        )

    return ElevenLabsAgentVerifyResponse(
        agent_id="elevenlabs_narration",
        agent_name="ElevenLabs Narration Agent",
        mp3_bytes=len(audio),
        detail="MP3 audio generated successfully (use this length as a sanity check).",
    )


def _build_behavior_prompt(agent_id: str) -> str:
    """Build a behavior-aware verification prompt per agent."""
    contract = get_contract(agent_id)
    if not contract:
        return "Reply in one short sentence confirming you are working."
    required = ", ".join(contract.required_keys)
    return (
        f"You are being tested as {agent_id}. "
        f"Respond with a valid JSON object containing these keys: {required}. "
        "Use realistic sample values. No prose outside the JSON."
    )


@router.post(
    "/verify/all",
    response_model=AgentHealthCheckResponse,
    summary="Behavior-aware verification across all registered agents",
)
def verify_all_agents() -> AgentHealthCheckResponse:
    registry = get_registry()
    if not registry.nodes:
        boot_registry()

    snapshot = registry.snapshot()
    results: list[AgentHealthCheckItem] = []

    ping_cache: dict[str, tuple[str, str, str | None]] = {}

    for node in snapshot["agents"]:
        agent_id = node["id"]
        agent_name = node["name"]
        model_type = node["model_type"]
        model = node["model_resolved"]
        runtime_kind = node["runtime_kind"]

        status = "ok"
        detail = "Agent ping succeeded."
        reply_preview: str | None = None

        behavior_prompt = _build_behavior_prompt(agent_id)

        if model_type in {
            "heavy",
            "heavy_alt",
            "light",
            "light_plus_scraper",
            "rule_plus_light",
            "hybrid",
            "light_plus_pgvector",
        }:
            selected_model = settings.light_model if model_type == "hybrid" else model
            has_specialization = agent_id in AGENT_CONTRACTS
            cache_key = f"llm::{selected_model}::{agent_id}" if has_specialization else f"llm::{selected_model}"
            if cache_key not in ping_cache:
                try:
                    from services.agents import get_agent_system_prompt
                    sys_prompt = get_agent_system_prompt(agent_id) if has_specialization else None
                    if not sys_prompt:
                        sys_prompt = "Reply in one short sentence like 'Hi, how can I help you?'"
                    actual_prompt = behavior_prompt if has_specialization else "hi"
                    token_limit = 800 if has_specialization else 80
                    reply = llm_chat_completion(
                        model=selected_model,
                        user_message=actual_prompt,
                        system_instruction=sys_prompt[:2000],
                        max_tokens=token_limit,
                    )

                    if has_specialization:
                        check_details: list[str] = []
                        json_valid = False
                        try:
                            clean_reply = re.sub(r'^```(?:json)?\s*', '', reply.strip())
                            clean_reply = re.sub(r'\s*```\s*$', '', clean_reply)
                            parsed = json.loads(clean_reply)
                            json_valid = True
                            contract = get_contract(agent_id)
                            if contract:
                                schema_valid, schema_errors = contract.validate_output(parsed)
                                if not schema_valid:
                                    check_details.append(f"schema: {schema_errors}")
                            envelope = normalize_agent_output(agent_id, clean_reply)
                            env_valid, env_errors = validate_envelope(envelope)
                            if not env_valid:
                                check_details.append(f"envelope: {env_errors}")
                        except json.JSONDecodeError:
                            check_details.append("Response is not valid JSON")

                        concise = len(reply) < 4000
                        if not concise:
                            check_details.append(f"Response too long: {len(reply)} chars")

                        if check_details:
                            detail_msg = f"Behavioral checks: {'; '.join(check_details)}"
                            cache_status = "ok" if json_valid else "failed"
                        else:
                            detail_msg = f"Behavior+schema+envelope OK ({len(reply)} chars)"
                            cache_status = "ok"

                        ping_cache[cache_key] = (cache_status, detail_msg, reply[:200])
                    else:
                        ping_cache[cache_key] = (
                            "ok",
                            f"LLM ping OK via {settings.llm_provider} model '{selected_model}'.",
                            reply[:200],
                        )
                except Exception as exc:
                    ping_cache[cache_key] = ("failed", str(exc), None)
            status, detail, reply_preview = ping_cache[cache_key]
        elif model_type in {"gemini_api", "gemini_vision"}:
            cache_key = f"gemini_or_light::{settings.gemini_model}::{settings.light_model}::{agent_id}"
            if cache_key not in ping_cache:
                try:
                    from services.agents import get_agent_system_prompt
                    sys_prompt = get_agent_system_prompt(agent_id)
                    reply, src = gemini_or_light_chat_completion_pair(
                        behavior_prompt,
                        system_instruction=sys_prompt[:2000] if sys_prompt else None,
                    )
                    clean_reply = re.sub(r'^```(?:json)?\s*', '', reply.strip())
                    clean_reply = re.sub(r'\s*```\s*$', '', clean_reply)
                    gemini_json_valid = False
                    try:
                        parsed_g = json.loads(clean_reply)
                        gemini_json_valid = True
                    except json.JSONDecodeError:
                        pass
                    via = "Gemini" if src == "gemini" else f"light model ({settings.light_model})"
                    ping_cache[cache_key] = (
                        "ok",
                        f"{via} behavior check OK ({len(reply)} chars, json={gemini_json_valid}).",
                        reply[:200],
                    )
                except ValueError as exc:
                    ping_cache[cache_key] = ("failed", str(exc), None)
                except Exception as exc:
                    ping_cache[cache_key] = ("failed", str(exc), None)
            status, detail, reply_preview = ping_cache[cache_key]
        elif model_type == "elevenlabs_api":
            cache_key = "elevenlabs::tts"
            if cache_key not in ping_cache:
                try:
                    audio = elevenlabs_synthesize_mp3("Hi, how can I help you?")
                    ping_cache[cache_key] = (
                        "ok",
                        f"ElevenLabs ping OK ({len(audio)} bytes mp3).",
                        f"{len(audio)} bytes mp3",
                    )
                except Exception as exc:
                    ping_cache[cache_key] = ("failed", str(exc), None)
            status, detail, reply_preview = ping_cache[cache_key]
        else:
            status = "skipped"
            detail = "System-service agent has no direct chat model endpoint."

        results.append(
            AgentHealthCheckItem(
                agent_id=agent_id,
                agent_name=agent_name,
                model_type=model_type,
                model=model,
                runtime_kind=runtime_kind,
                status=status,
                detail=detail,
                reply_preview=reply_preview,
            ),
        )

    checks_total = len(results)
    checks_passed = sum(1 for r in results if r.status == "ok")
    checks_failed = sum(1 for r in results if r.status == "failed")
    checks_skipped = sum(1 for r in results if r.status == "skipped")
    overall = "ok" if checks_failed == 0 else "degraded"

    return AgentHealthCheckResponse(
        status=overall,
        checks_total=checks_total,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        checks_skipped=checks_skipped,
        results=results,
    )


@router.post("/mvp", response_model=AgentMVPResponse)
def build_agents_mvp(payload: AgentMVPRequest) -> AgentMVPResponse:
    registry = get_registry()
    if not registry.nodes:
        boot_registry()

    try:
        if payload.run:
            result = kickoff_mvp(
                user_goal=payload.user_goal,
                company_context=payload.company_context,
            )
        else:
            result = initialize_only_mvp(
                user_goal=payload.user_goal,
                company_context=payload.company_context,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CrewAI MVP failed: {exc}") from exc

    registry_snapshot = registry.snapshot()
    registry_agent_names = [node["name"] for node in registry_snapshot["agents"]]

    return AgentMVPResponse(
        status="ok",
        run_executed=payload.run,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        heavy_model=settings.heavy_model,
        heavy_alt_model=settings.heavy_alt_model,
        light_model=settings.light_model,
        embedding_model=settings.embedding_model,
        agents_initialized=registry_agent_names,
        tasks_initialized=result["tasks_initialized"],
        output=result["output"],
    )


@router.post("/specialized", response_model=AgentMVPResponse)
def run_specialized_agents(payload: AgentMVPRequest) -> AgentMVPResponse:
    """Run specialized agents using per-agent modules instead of MVP crew."""
    registry = get_registry()
    if not registry.nodes:
        boot_registry()

    try:
        if payload.run:
            result = kickoff_specialized(
                user_goal=payload.user_goal,
                company_context=payload.company_context,
            )
        else:
            result = initialize_specialized(
                user_goal=payload.user_goal,
                company_context=payload.company_context,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Specialized crew failed: {exc}") from exc

    registry_snapshot = registry.snapshot()
    registry_agent_names = [node["name"] for node in registry_snapshot["agents"]]

    return AgentMVPResponse(
        status="ok",
        run_executed=payload.run,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        heavy_model=settings.heavy_model,
        heavy_alt_model=settings.heavy_alt_model,
        light_model=settings.light_model,
        embedding_model=settings.embedding_model,
        agents_initialized=registry_agent_names,
        tasks_initialized=result["tasks_initialized"],
        output=result["output"],
    )


@router.get("/ollama-catalog", response_model=OllamaCatalogResponse)
def ollama_catalog() -> OllamaCatalogResponse:
    key_ok = settings.llm_api_key_configured
    sanity = (
        "LLM_API_KEY is set; Featherless inference should work for run=true."
        if key_ok
        else "Set LLM_API_KEY in apps/api/.env (Featherless API key). Init/boot works; live generation will fail until the key is set."
    )
    return OllamaCatalogResponse(
        hardware_summary=HARDWARE_SUMMARY,
        defaults={
            "llm_provider": settings.llm_provider,
            "llm_base_url": settings.llm_base_url,
            "heavy_model": settings.heavy_model,
            "heavy_alt_model": settings.heavy_alt_model,
            "light_model": settings.light_model,
            "embedding_model": settings.embedding_model,
        },
        models=MODELS,
        pull_commands=pull_commands(),
        llm_api_key_configured=key_ok,
        llm_sanity_message=sanity,
    )
