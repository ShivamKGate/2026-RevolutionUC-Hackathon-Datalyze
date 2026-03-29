"""Plain Text Processor Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "plain_text_processor"
AGENT_NAME = "Plain Text Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 500

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="plain text chunking and tagging only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You process plain text, markdown, and log-like inputs into clean "
        "semantic chunks.\n\n"
        "Break content into meaningful segments, assign semantic tags "
        "(narrative, log_entry, list, heading, code_block), and detect "
        "the primary language if identifiable.\n\n"
        "Output schema:\n"
        "{\n"
        '  "chunks": [{"chunk_id": "...", "content": "...", "tag": "narrative|log_entry|list|heading|code_block"}],\n'
        '  "column_metadata": [],\n'
        '  "data_preview": {"sample_chunks": [{"chunk_id": "...", "tag": "narrative", "content": "..."}]},\n'
        '  "detected_schema": {"document_type": "notes|report|logs|mixed", "semantic_tag_counts": {"narrative": N}},\n'
        '  "semantic_tags": ["narrative", "list"],\n'
        '  "chart_suggestions": ["tag_distribution_bar", "kpi_card"]\n'
        "}\n\n"
        "Keep chunks between 100-500 tokens each for downstream processing efficiency."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["chunks", "column_metadata", "data_preview", "detected_schema", "semantic_tags", "chart_suggestions"],
    "optional": ["language_detected", "line_count"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Extract and chunk plain text with semantic tags.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Process the plain text input into semantic chunks with tags. "
            "Include data_preview, detected_schema, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: chunks, column_metadata, data_preview, detected_schema, semantic_tags, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
