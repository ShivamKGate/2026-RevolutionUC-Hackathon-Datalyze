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
        "confidence score, chart hint, and structured data payload suitable for rendering.\n\n"
        "Output schema:\n"
        "{\n"
        '  "insights": [\n'
        "    {\n"
        '      "title": "string",\n'
        '      "description": "string",\n'
        '      "impact": "low|medium|high",\n'
        '      "confidence": 0.0-1.0,\n'
        '      "chart_type": "kpi_card|bar_chart|line_chart|radar|heatmap|table",\n'
        '      "data": {"current": N, "previous": N, "change_pct": N},\n'
        '      "provenance": ["source_id1", "source_id2"]\n'
        "    }\n"
        "  ],\n"
        '  "recommendations": [\n'
        '    {"action": "string", "priority": "low|medium|high", "expected_impact": "string", "confidence": 0.0-1.0}\n'
        "  ],\n"
        '  "chart_suggestions": ["kpi_card", "insight_bar_chart", "recommendation_table"]\n'
        "}\n\n"
        "Prioritize actionable insights over observational ones. "
        "Surface recommendations only when confidence is >= 0.6. "
        "Every insight and recommendation must be grounded in provided data — no speculation."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["insights", "recommendations", "chart_suggestions"],
    "optional": ["impact_rankings"],
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
            "conflicts, sentiment, and forecasts. Each must include provenance, chart_type, "
            "and structured data payload. Include recommendations with confidence >= 0.6 "
            "and include chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: insights, recommendations, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
