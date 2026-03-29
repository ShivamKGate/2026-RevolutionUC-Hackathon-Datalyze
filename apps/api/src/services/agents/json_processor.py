"""JSON Processor Agent — strict, rule+light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "json_processor"
AGENT_NAME = "JSON Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="JSON flattening and structure mapping only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You process JSON documents by flattening nested structures into "
        "usable records and mapping parent-child relationships.\n\n"
        "Detect top-level structure (object vs array), enumerate nested "
        "paths, and produce flattened records suitable for tabular analysis.\n\n"
        "Output schema:\n"
        "{\n"
        '  "records": [{"path": "root.field.subfield", "value": ..., "type": "string|number|bool|null|array|object"}],\n'
        '  "column_metadata": [{"path": "root.a.b", "type": "string|number|bool|null|array|object"}],\n'
        '  "data_preview": {"sample_records": [{"path": "root.a", "value": "..."}]},\n'
        '  "detected_schema": {"max_depth": N, "time_fields": ["root.date"], "measure_fields": ["root.revenue"]},\n'
        '  "nested_map": {"max_depth": N, "paths": ["root.a", "root.a.b", ...]},\n'
        '  "chart_suggestions": ["kpi_card", "bar_chart", "time_series_chart"]\n'
        "}\n\n"
        "Keep parent-child path references for provenance tracking."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["records", "column_metadata", "data_preview", "detected_schema", "nested_map", "chart_suggestions"],
    "optional": ["array_lengths", "depth"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Flatten and normalize JSON documents into usable records.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Process the JSON document, flatten nested structures, and map "
            "parent-child relationships. "
            "Include column_metadata, data_preview, detected_schema, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: records, column_metadata, data_preview, detected_schema, nested_map, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
