"""Aggregator Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "aggregator"
AGENT_NAME = "Aggregator Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 1200

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="evidence aggregation and prioritization",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You aggregate cleaned, categorized data chunks and scraper artifacts "
        "into a structured analysis corpus.\n\n"
        "Prioritize evidence by relevance and assign usefulness scores (0-100). "
        "Generate storyline hypotheses that connect related data points. "
        "Retain low-value data but deprioritize it.\n\n"
        "Output schema:\n"
        "{\n"
        '  "corpus": [{"item_id": "...", "content_summary": "...", "source": "...", "relevance_score": 0-100}],\n'
        '  "usefulness_scores": {"high": N, "medium": N, "low": N},\n'
        '  "storyline_hypotheses": ["Hypothesis 1: ...", "Hypothesis 2: ..."]\n'
        "}\n\n"
        "Ground all hypotheses in cited evidence items."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["corpus", "usefulness_scores", "storyline_hypotheses"],
    "optional": ["low_value_retained", "source_distribution"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Aggregate and prioritize evidence into a synthesis-ready corpus.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Aggregate the cleaned and categorized data with scraper artifacts. "
            "Prioritize evidence, score usefulness, and generate storyline hypotheses. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: corpus, usefulness_scores, storyline_hypotheses',
        agent=agent,
        context=context_tasks or [],
    )
