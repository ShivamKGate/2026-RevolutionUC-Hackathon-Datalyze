"""Public Data Scraper Agent — strict, light+scraper."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "public_data_scraper"
AGENT_NAME = "Public Data Scraper Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 1000

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="public data gathering and source tagging only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You gather publicly available data aligned to the analysis track objective.\n\n"
        "Given a track profile and company context, identify and retrieve relevant "
        "public evidence: news articles, SEC filings, industry reports, competitor data, "
        "social media signals, etc.\n\n"
        "Tag each artifact with source URL, retrieval timestamp, and credibility assessment.\n\n"
        "Output schema:\n"
        "{\n"
        '  "artifacts": [{"title": "...", "source_url": "...", "content_summary": "...", '
        '"retrieved_at": "ISO8601", "credibility": "high|medium|low"}],\n'
        '  "sources": ["url1", "url2"],\n'
        '  "credibility_tags": {"high": N, "medium": N, "low": N}\n'
        "}\n\n"
        "Respect bounded crawl depth. Only surface relevant, verifiable sources."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["artifacts", "sources", "credibility_tags"],
    "optional": ["crawl_depth", "warnings"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Gather public evidence aligned to track objective with credibility tags.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Based on the track profile and company context, gather relevant public data "
            "artifacts with source metadata and credibility assessments. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: artifacts, sources, credibility_tags',
        agent=agent,
        context=context_tasks or [],
    )
