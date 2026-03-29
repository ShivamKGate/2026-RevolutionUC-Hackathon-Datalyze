"""Smart Categorizer / Metadata Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "smart_categorizer_metadata"
AGENT_NAME = "Smart Categorizer / Metadata Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 500

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="domain categorization and metadata tagging only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You categorize cleaned data chunks by business domain and content type.\n\n"
        "Assign multi-label domain tags from a controlled vocabulary: "
        "finance, hr, operations, marketing, sales, legal, compliance, "
        "technology, customer_service, strategy.\n\n"
        "Assign content-type tags: quantitative, qualitative, temporal, "
        "categorical, text_narrative, structured_data.\n\n"
        "Output schema:\n"
        "{\n"
        '  "domain_tags": [{"chunk_id": "...", "domains": ["finance", "operations"], "confidence": 0.0-1.0}],\n'
        '  "content_type_tags": [{"chunk_id": "...", "types": ["quantitative", "temporal"]}]\n'
        "}\n\n"
        "Multi-label tagging allowed — a chunk can belong to multiple domains."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["domain_tags", "content_type_tags"],
    "optional": ["multi_label_map", "tag_confidence"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Tag cleaned chunks with domain and content-type metadata.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Categorize the cleaned chunks with domain tags and content-type tags. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: domain_tags, content_type_tags',
        agent=agent,
        context=context_tasks or [],
    )
