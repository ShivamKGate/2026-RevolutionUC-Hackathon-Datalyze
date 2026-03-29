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
        "Produce 2-3 concrete automation suggestions, each with a clear "
        "implementation path (2-3 steps), feasibility assessment, and "
        "expected impact.\n\n"
        "Output schema:\n"
        "{\n"
        '  "suggestions": [{"title": "...", "description": "...", "steps": ["Step 1", "Step 2"], '
        '"feasibility": "high|medium|low", "expected_impact": "...", '
        '"prerequisites": ["..."]}]\n'
        "}\n\n"
        "Suggestions only — no full implementation. "
        "Focus on actionable, practical automation for the specific business."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["suggestions"],
    "optional": ["feasibility_scores", "implementation_steps", "prerequisites"],
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
            "Based on operations evidence, recommend 2-3 practical automation "
            "opportunities with implementation steps and feasibility assessment. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with key: suggestions (array of suggestion objects)',
        agent=agent,
        context=context_tasks or [],
    )
