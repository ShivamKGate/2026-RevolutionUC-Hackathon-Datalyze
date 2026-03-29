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
        "The summary must be concise (150-300 words), actionable, and suitable "
        "for export. Include key findings, risk highlights, and 2-3 immediate "
        "next actions.\n\n"
        "Output schema:\n"
        "{\n"
        '  "summary": "Board-ready summary paragraph...",\n'
        '  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],\n'
        '  "next_actions": ["Action 1", "Action 2"]\n'
        "}\n\n"
        "Use professional, direct language. Avoid jargon. "
        "Export-safe formatting (no markdown, no special characters)."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["summary", "key_findings", "next_actions"],
    "optional": ["risk_highlights", "confidence_statement"],
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
            "Write a concise executive summary with key findings and 2-3 "
            "immediate next actions based on the analysis results. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: summary, key_findings, next_actions',
        agent=agent,
        context=context_tasks or [],
    )
