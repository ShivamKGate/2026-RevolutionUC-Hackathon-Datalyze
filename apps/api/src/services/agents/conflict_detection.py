"""Conflict Detection Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "conflict_detection"
AGENT_NAME = "Conflict Detection Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="contradiction and conflict detection only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You detect contradictions and conflicts within an aggregated data corpus.\n\n"
        "Compare data points for logical inconsistencies, numerical conflicts, "
        "contradicting statements, and temporal impossibilities. "
        "Report each contradiction with supporting references from both sides.\n\n"
        "Output schema:\n"
        "{\n"
        '  "contradictions": [{"id": "...", "description": "...", "side_a": "...", '
        '"side_b": "...", "severity": "high|medium|low", "confidence": 0.0-1.0}],\n'
        '  "supporting_references": [{"contradiction_id": "...", "source_items": ["item_id1", "item_id2"]}]\n'
        "}\n\n"
        "Only report genuine conflicts, not differences in granularity or perspective."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["contradictions", "supporting_references"],
    "optional": ["severity_levels", "confidence"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Detect contradictions and conflicts in aggregated data.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Analyze the aggregated corpus for contradictions and conflicts. "
            "Report each with severity, confidence, and supporting references. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: contradictions, supporting_references',
        agent=agent,
        context=context_tasks or [],
    )
