"""
Modular specialized agent runtime — replaces crew_mvp.py for specialization paths.

Uses per-agent modules from services.agents instead of inline agent definitions.
Model assignment comes from agent_registry; agent behavior from per-agent modules.
Output normalization bridges to orchestrator adapter envelope via normalizer.

crew_mvp.py is preserved as a compatibility alias during transition.
"""

from __future__ import annotations

import json
import os
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task

from core.config import settings
from services.agents import get_agent_module
from services.agents.normalizer import normalize_agent_output


def _normalize_model(model: str) -> str:
    normalized = model.strip()
    # Route org/model slugs through OpenAI-compatible provider (Featherless).
    if "/" in normalized and not normalized.startswith(("openai/", "azure/", "gemini/")):
        return f"openai/{normalized}"
    return normalized


def _prime_crewai_env() -> None:
    """CrewAI reads OPENAI_* env vars internally for its LLM wire protocol. We
    point them to Featherless (OpenAI-compatible base URL + API key)."""
    os.environ.setdefault("OPENAI_BASE_URL", settings.llm_base_url)
    os.environ.setdefault("OPENAI_API_KEY", settings.llm_api_key or "DATALYZE_PLACEHOLDER_KEY")


def _build_llm(model_name: str) -> LLM:
    _prime_crewai_env()
    return LLM(
        model=_normalize_model(model_name),
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


def build_specialized_crew(
    user_goal: str,
    company_context: str,
    agent_ids: list[str] | None = None,
) -> tuple[Crew, list[Task], list[Agent]]:
    """Build a crew using per-agent specialized modules.

    If agent_ids is None, uses the default MVP sequence:
    aggregator -> insight_generation -> executive_summary.
    """
    if agent_ids is None:
        agent_ids = ["aggregator", "insight_generation", "executive_summary"]

    llm_heavy_alt = _build_llm(settings.heavy_alt_model)
    llm_light = _build_llm(settings.light_model)

    agents: list[Agent] = []
    tasks: list[Task] = []

    for agent_id in agent_ids:
        mod = get_agent_module(agent_id)
        if mod is None:
            continue

        spec_model_type = _get_model_type_for_agent(agent_id)
        if spec_model_type in ("heavy", "heavy_alt"):
            llm = llm_heavy_alt
        else:
            llm = llm_light

        agent = mod.build_agent(llm)
        context_tasks = tasks[-1:] if tasks else []
        task = mod.build_task(agent, context_tasks)

        agents.append(agent)
        tasks.append(task)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )
    return crew, tasks, agents


def _get_model_type_for_agent(agent_id: str) -> str:
    from services.agent_registry import get_registry
    registry = get_registry()
    spec = registry.specs_by_id.get(agent_id)
    return spec.model_type if spec else "light"


def kickoff_specialized(
    user_goal: str,
    company_context: str,
    agent_ids: list[str] | None = None,
) -> dict[str, Any]:
    crew, tasks, agents = build_specialized_crew(
        user_goal=user_goal,
        company_context=company_context,
        agent_ids=agent_ids,
    )
    result = crew.kickoff(
        inputs={
            "user_goal": user_goal,
            "company_context": company_context,
        }
    )

    output_text = getattr(result, "raw", None) or getattr(result, "output", None) or str(result)

    normalized_results: list[dict[str, Any]] = []
    for agent_id in (agent_ids or ["aggregator", "insight_generation", "executive_summary"]):
        envelope = normalize_agent_output(agent_id, output_text)
        normalized_results.append({"agent_id": agent_id, "envelope": envelope})

    return {
        "agents_initialized": [a.role for a in agents],
        "tasks_initialized": len(tasks),
        "output": output_text,
        "normalized_envelopes": normalized_results,
    }


def initialize_specialized(
    user_goal: str,
    company_context: str,
    agent_ids: list[str] | None = None,
) -> dict[str, Any]:
    _, tasks, agents = build_specialized_crew(
        user_goal=user_goal,
        company_context=company_context,
        agent_ids=agent_ids,
    )
    return {
        "agents_initialized": [a.role for a in agents],
        "tasks_initialized": len(tasks),
        "output": None,
        "normalized_envelopes": [],
    }


def run_single_agent(
    agent_id: str,
    input_text: str,
    system_override: str | None = None,
) -> dict[str, Any]:
    """Run a single specialized agent and return normalized output."""
    mod = get_agent_module(agent_id)
    if mod is None:
        return normalize_agent_output(agent_id, {"errors": [f"No module for agent: {agent_id}"]})

    model_type = _get_model_type_for_agent(agent_id)
    if model_type in ("heavy", "heavy_alt"):
        llm = _build_llm(settings.heavy_alt_model)
    else:
        llm = _build_llm(settings.light_model)

    agent = mod.build_agent(llm)
    task = Task(
        description=input_text,
        expected_output="JSON object matching agent schema",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()

    output_text = getattr(result, "raw", None) or getattr(result, "output", None) or str(result)
    return normalize_agent_output(agent_id, output_text)
