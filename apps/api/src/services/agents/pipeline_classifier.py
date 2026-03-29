"""Pipeline Classifier Agent — strict, Gemini API.

Rich track classification for orchestrator: reasoning, file/domain signals,
recommended_agents / skip_agents, plus priority_map and scraper_strategy.
"""

from __future__ import annotations

from typing import Any

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "pipeline_classifier"
AGENT_NAME = "Pipeline Classifier Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="track classification and priority mapping only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You classify the analysis pipeline track from onboarding, company context, "
        "stated goals, AND any file manifest or file-content summaries provided "
        "(not just file counts). Use summaries to infer domains (e.g. sales, HR), "
        "formats (excel, pdf), and whether forecasting, automation, or supply signals apply.\n\n"
        "Select exactly one primary track from: "
        "'predictive', 'automation', 'optimization', 'supply_chain'.\n\n"
        "Optionally set secondary_track to another track from the same list that is "
        "also relevant, or the empty string \"\" if none.\n\n"
        "You MUST output:\n"
        "- confidence: 0.0–1.0 for the primary track choice.\n"
        "- reasoning: one concise paragraph explaining why (cite goals and file evidence when present).\n"
        "- file_types_detected: inferred file categories (e.g. excel, pdf, csv, image, json, text).\n"
        "- data_domains_detected: business domains implied by content (e.g. sales, finance, operations, HR).\n"
        "- recommended_agents: agent_ids to emphasize for this run (subset of registry agents; "
        "e.g. trend_forecasting, insight_generation, automation_strategy, sentiment_analysis).\n"
        "- skip_agents: agent_ids that are low value for this track and should be skipped if the "
        "orchestrator supports it (e.g. automation_strategy when track is purely predictive).\n"
        "- priority_map: map agent_id -> integer priority 1–10 (10 = highest).\n"
        "- scraper_strategy: {focus_keywords, industry_vertical, depth: shallow|moderate|deep} "
        "for public data collection.\n\n"
        "Output schema:\n"
        "{\n"
        '  "track": "predictive|automation|optimization|supply_chain",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "reasoning": "string",\n'
        '  "secondary_track": "predictive|automation|optimization|supply_chain|",\n'
        '  "file_types_detected": ["excel", "pdf"],\n'
        '  "data_domains_detected": ["sales", "finance"],\n'
        '  "recommended_agents": ["trend_forecasting", "insight_generation"],\n'
        '  "skip_agents": ["automation_strategy"],\n'
        '  "priority_map": {"trend_forecasting": 10, "insight_generation": 8},\n'
        '  "scraper_strategy": {"focus_keywords": ["..."], "industry_vertical": "...", "depth": "moderate"},\n'
        '  "vision_fallback": false\n'
        "}\n\n"
        "recommended_agents and skip_agents must be disjoint. "
        "If the input mentions images/PDFs needing vision, set vision_fallback to true "
        "but still return full JSON."
    ),
)

OUTPUT_SCHEMA = {
    "required": [
        "track",
        "confidence",
        "reasoning",
        "secondary_track",
        "file_types_detected",
        "data_domains_detected",
        "recommended_agents",
        "skip_agents",
        "priority_map",
        "scraper_strategy",
    ],
    "optional": ["vision_fallback"],
}


def build_agent(llm: Any) -> Any:
    from crewai import Agent

    return Agent(
        role=AGENT_NAME,
        goal="Classify the pipeline track with rich metadata for downstream orchestration.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Any, context_tasks: list[Any] | None = None) -> Any:
    from crewai import Task

    return Task(
        description=(
            "Given onboarding, company context, goals, and any FILE SUMMARIES or manifest "
            "(not only counts), classify the track with confidence, reasoning, "
            "file_types_detected, data_domains_detected, recommended_agents, skip_agents, "
            "priority_map, and scraper_strategy. Return ONLY a JSON object matching the schema."
        ),
        expected_output=(
            "JSON with keys: track, confidence, reasoning, secondary_track, "
            "file_types_detected, data_domains_detected, recommended_agents, skip_agents, "
            "priority_map, scraper_strategy"
        ),
        agent=agent,
        context=context_tasks or [],
    )
