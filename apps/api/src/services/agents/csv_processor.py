"""CSV Processor Agent — strict, rule+light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "csv_processor"
AGENT_NAME = "CSV Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="CSV parsing and schema inference only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You parse CSV files and produce structured data summaries.\n\n"
        "Detect delimiter, header row, and encoding. Infer column types "
        "(string, numeric, date, boolean). Compute basic summary statistics "
        "for numeric columns (min, max, mean, count, null_count).\n\n"
        "Output schema:\n"
        "{\n"
        '  "rows_summary": {"total_rows": N, "sample_rows": [[...], ...]},\n'
        '  "inferred_schema": [{"column": "name", "type": "string|numeric|date|boolean", "nullable": true|false}],\n'
        '  "stats": [{"column": "name", "min": ..., "max": ..., "mean": ..., "null_count": N}]\n'
        "}\n\n"
        "Flag header anomalies or delimiter ambiguities in optional fields."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["rows_summary", "inferred_schema", "stats"],
    "optional": ["delimiter", "header_anomalies", "encoding"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Parse CSV files and infer schema with summary statistics.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Parse the provided CSV data, detect schema and delimiter, "
            "compute summary statistics for numeric columns. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: rows_summary, inferred_schema, stats',
        agent=agent,
        context=context_tasks or [],
    )
