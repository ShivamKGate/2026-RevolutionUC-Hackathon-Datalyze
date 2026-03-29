"""Data Cleaning Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "data_cleaning"
AGENT_NAME = "Data Cleaning Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="data normalization and deduplication only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You clean and normalize raw extracted data chunks before aggregation.\n\n"
        "Apply: date format standardization (ISO 8601), number format normalization, "
        "encoding cleanup (UTF-8), duplicate detection and flagging, "
        "whitespace/formatting cleanup, and null/empty value handling.\n\n"
        "Output schema:\n"
        "{\n"
        '  "cleaned_chunks": [{"chunk_id": "...", "content": "...", "cleaning_applied": ["dedup", "date_norm"]}],\n'
        '  "dedup_flags": [{"original_id": "...", "duplicate_of": "...", "similarity": 0.0-1.0}],\n'
        '  "normalization_applied": ["date_format", "encoding_fix", "whitespace_cleanup"]\n'
        "}\n\n"
        "Preserve original chunk IDs for provenance tracking."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["cleaned_chunks", "dedup_flags", "normalization_applied"],
    "optional": ["encoding_fixes", "format_corrections"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Clean, normalize, and deduplicate raw data chunks.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Clean the raw extracted chunks: normalize dates, fix encoding, "
            "remove duplicates, standardize formats. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: cleaned_chunks, dedup_flags, normalization_applied',
        agent=agent,
        context=context_tasks or [],
    )
