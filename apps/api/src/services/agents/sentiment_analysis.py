"""Sentiment Analysis Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "sentiment_analysis"
AGENT_NAME = "Sentiment Analysis Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="sentiment classification and trend summarization only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You classify sentiment in feedback, review, and social text data.\n\n"
        "For each text segment, assign a sentiment label (positive, negative, neutral, mixed) "
        "with a confidence score. Summarize overall sentiment trends across the corpus.\n\n"
        "Output schema:\n"
        "{\n"
        '  "sentiments": [{"text_id": "...", "label": "positive|negative|neutral|mixed", '
        '"confidence": 0.0-1.0, "key_phrases": ["..."]}],\n'
        '  "trend_summary": {"positive_pct": N, "negative_pct": N, "neutral_pct": N, '
        '"overall_direction": "improving|declining|stable"}\n'
        "}\n\n"
        "Track source channel metadata when available."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["sentiments", "trend_summary"],
    "optional": ["chart_payloads", "source_channels", "sample_quotes"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Classify sentiment and summarize trends from text data.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Classify sentiment for each text segment and summarize overall trends. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: sentiments, trend_summary',
        agent=agent,
        context=context_tasks or [],
    )
