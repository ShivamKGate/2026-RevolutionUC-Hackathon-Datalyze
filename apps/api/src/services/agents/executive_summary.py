"""Executive Summary Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "executive_summary"
AGENT_NAME = "Executive Summary Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="board-ready executive summary synthesis",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You produce a board-ready executive summary from finalized insights, "
        "SWOT analysis, and risk/conflict highlights.\n\n"
        "The summary must be concise, actionable, and suitable for export. "
        "Return structured sections (not a single long paragraph).\n\n"
        "Output schema:\n"
        "{\n"
        '  "headline": "string",\n'
        '  "situation_overview": "string",\n'
        '  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],\n'
        '  "risk_highlights": ["Risk 1", "Risk 2"],\n'
        '  "next_actions": ["Action 1", "Action 2"],\n'
        '  "confidence_statement": {"overall_confidence": 0.0-1.0, "basis": "string"},\n'
        '  "chart_suggestions": ["executive_kpi_cards", "risk_priority_table"]\n'
        "}\n\n"
        "Use professional, direct language. Avoid jargon. "
        "Export-safe formatting (no markdown, no special characters)."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["headline", "situation_overview", "key_findings", "risk_highlights", "next_actions", "confidence_statement", "chart_suggestions"],
    "optional": [],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Produce a board-ready executive summary with actionable next steps.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Write a concise executive summary in structured sections with key findings, "
            "risk highlights, next actions, confidence statement, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: headline, situation_overview, key_findings, risk_highlights, next_actions, confidence_statement, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
