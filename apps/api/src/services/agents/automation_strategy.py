"""Automation Strategy Agent — guarded, hybrid."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "automation_strategy"
AGENT_NAME = "Automation Strategy Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="automation opportunity recommendation",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You recommend practical automation opportunities based on operations "
        "and process evidence from the aggregated corpus.\n\n"
        "Analyze process candidates and return structured process-level "
        "automation opportunities with bottlenecks and SOP drafting hints.\n\n"
        "Output schema:\n"
        "{\n"
        '  "processes": [\n'
        "    {\n"
        '      "name": "string",\n'
        '      "current_time_hours": N,\n'
        '      "automated_time_hours": N,\n'
        '      "cost_current": N,\n'
        '      "cost_automated": N,\n'
        '      "roi_months": N,\n'
        '      "implementation_effort": "low|medium|high",\n'
        '      "impact_score": 0.0-1.0\n'
        "    }\n"
        "  ],\n"
        '  "bottlenecks": [{"stage": "string", "time_pct": N, "cost_pct": N}],\n'
        '  "sop_draft": {"steps": ["string"], "estimated_savings_annual": N},\n'
        '  "chart_suggestions": ["process_sankey", "roi_bubble_chart", "automation_matrix"]\n'
        "}\n\n"
        "Focus on actionable, practical automation for the specific business. "
        "Use realistic ranges grounded in provided evidence and avoid speculative extremes."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["processes", "bottlenecks", "sop_draft", "chart_suggestions"],
    "optional": [],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Recommend practical automation opportunities with implementation steps.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Based on operations evidence, analyze automation opportunities and return "
            "process metrics, bottlenecks, SOP draft, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: processes, bottlenecks, sop_draft, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
