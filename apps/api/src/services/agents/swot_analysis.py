"""SWOT Analysis Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "swot_analysis"
AGENT_NAME = "SWOT Analysis Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 1000

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="SWOT quadrant analysis grounded in evidence",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You produce a structured SWOT analysis from insights and aggregated evidence.\n\n"
        "For each quadrant (Strengths, Weaknesses, Opportunities, Threats), "
        "provide 2-5 items grounded in cited evidence. Each item must reference "
        "specific data points or insights.\n\n"
        "Output schema:\n"
        "{\n"
        '  "strengths": [{"item": "...", "evidence": "...", "confidence": "high|medium|low"}],\n'
        '  "weaknesses": [{"item": "...", "evidence": "...", "confidence": "high|medium|low"}],\n'
        '  "opportunities": [{"item": "...", "evidence": "...", "confidence": "high|medium|low"}],\n'
        '  "threats": [{"item": "...", "evidence": "...", "confidence": "high|medium|low"}]\n'
        "}\n\n"
        "Ground every SWOT item in cited evidence. No unsupported claims."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["strengths", "weaknesses", "opportunities", "threats"],
    "optional": ["evidence_citations", "priority_scores"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Produce evidence-grounded SWOT quadrant analysis.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Produce a SWOT analysis with 2-5 evidence-grounded items per quadrant. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: strengths, weaknesses, opportunities, threats',
        agent=agent,
        context=context_tasks or [],
    )
