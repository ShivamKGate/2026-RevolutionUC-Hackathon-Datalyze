from fastapi import APIRouter, HTTPException

from core.config import settings
from core.ollama_models import HARDWARE_SUMMARY, MODELS, pull_commands
from schemas.agents import AgentMVPRequest, AgentMVPResponse
from schemas.ollama_catalog import OllamaCatalogResponse
from services.crew_mvp import initialize_only_mvp, kickoff_mvp

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/mvp", response_model=AgentMVPResponse)
def build_agents_mvp(payload: AgentMVPRequest) -> AgentMVPResponse:
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

    return AgentMVPResponse(
        status="ok",
        run_executed=payload.run,
        ollama_host=settings.ollama_host,
        heavy_model=settings.heavy_model,
        light_model=settings.light_model,
        embedding_model=settings.embedding_model,
        agents_initialized=result["agents_initialized"],
        tasks_initialized=result["tasks_initialized"],
        output=result["output"],
    )


@router.get("/ollama-catalog", response_model=OllamaCatalogResponse)
def ollama_catalog() -> OllamaCatalogResponse:
    return OllamaCatalogResponse(
        hardware_summary=HARDWARE_SUMMARY,
        defaults={
            "ollama_host": settings.ollama_host,
            "heavy_model": settings.heavy_model,
            "light_model": settings.light_model,
            "embedding_model": settings.embedding_model,
        },
        models=MODELS,
        pull_commands=pull_commands(),
    )
