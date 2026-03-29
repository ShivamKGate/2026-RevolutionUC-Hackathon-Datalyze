"""Pipeline Classifier Agent — strict, Gemini API."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "pipeline_classifier"
AGENT_NAME = "Pipeline Classifier Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="track classification and priority mapping only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You classify the analysis pipeline track based on onboarding responses, "
        "company context, and user-selected goals.\n\n"
        "Your output determines which analysis path the system follows. "
        "You MUST select exactly one track from: "
        "'financial_analysis', 'operations_optimization', 'market_research', 'general_analytics'.\n\n"
        "For each track, produce a priority map ranking which downstream agents "
        "should receive the highest emphasis, and a scraper targeting strategy "
        "that guides public data collection focus.\n\n"
        "Output schema:\n"
        "{\n"
        '  "track": "<one of the four tracks>",\n'
        '  "priority_map": {"<agent_id>": <priority_int_1_to_10>, ...},\n'
        '  "scraper_strategy": {"focus_keywords": [...], "industry_vertical": "...", "depth": "shallow|moderate|deep"},\n'
        '  "confidence": <0.0-1.0>\n'
        "}\n\n"
        "If the input includes images/PDFs, note vision_fallback=true but still produce the classification."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["track", "priority_map", "scraper_strategy"],
    "optional": ["vision_fallback", "confidence"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Classify the pipeline track and produce priority mappings for downstream agents.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Given the onboarding responses and company context, classify the analysis "
            "track and produce a priority map with scraper targeting strategy. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: track, priority_map, scraper_strategy',
        agent=agent,
        context=context_tasks or [],
    )
