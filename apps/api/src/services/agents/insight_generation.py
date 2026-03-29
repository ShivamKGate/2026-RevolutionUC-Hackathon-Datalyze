"""Insight Generation Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "insight_generation"
AGENT_NAME = "Insight Generation Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 1000

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="business insight synthesis from aggregated evidence",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You synthesize business insights from aggregated evidence, conflict signals, "
        "sentiment trends, and forecasts.\n\n"
        "Produce 3-7 insight cards, each with a clear title, business impact description, "
        "confidence level, and provenance tags linking back to source evidence.\n\n"
        "Output schema:\n"
        "{\n"
        '  "insights": [{"title": "...", "impact": "...", "confidence": "high|medium|low", '
        '"provenance": ["source_id1", "source_id2"], "category": "risk|opportunity|trend|finding"}]\n'
        "}\n\n"
        "Prioritize actionable insights over observational ones. "
        "Every insight must be grounded in provided data — no speculation."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["insights"],
    "optional": ["provenance_tags", "confidence_scores", "impact_rankings"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Generate actionable business insights with provenance.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Synthesize 3-7 business insights from aggregated evidence, "
            "conflicts, sentiment, and forecasts. Each must include provenance. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with key: insights (array of insight objects)',
        agent=agent,
        context=context_tasks or [],
    )
