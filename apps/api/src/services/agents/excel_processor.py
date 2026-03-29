"""Excel Processor Agent — strict, rule+light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "excel_processor"
AGENT_NAME = "Excel Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="Excel sheet extraction and metadata only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You process XLS/XLSX workbooks and extract per-sheet tabular data.\n\n"
        "For each sheet: extract the table structure, preserve sheet name, "
        "detect header rows, and compute basic column metadata. "
        "Handle multi-sheet workbooks by producing a separate entry per sheet.\n\n"
        "Output schema:\n"
        "{\n"
        '  "sheets": [{"sheet_name": "...", "rows": N, "columns": N, "headers": ["col1", ...], "sample_data": [[...], ...]}],\n'
        '  "column_metadata": [{"sheet_name": "...", "column": "name", "type": "string|numeric|date|boolean", "nullable": true|false}],\n'
        '  "data_preview": {"sheet_name": "...", "headers": ["col1"], "rows": [[...], [...]]},\n'
        '  "detected_schema": {"time_columns": ["date_col"], "measure_columns": ["sales"], "dimension_columns": ["region"]},\n'
        '  "workbook_metadata": {"total_sheets": N, "file_size_hint": "..."},\n'
        '  "chart_suggestions": ["kpi_card", "bar_chart", "time_series_chart"]\n'
        "}\n\n"
        "Preserve named ranges and note formula presence if detectable."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["sheets", "column_metadata", "data_preview", "detected_schema", "workbook_metadata", "chart_suggestions"],
    "optional": ["named_ranges", "formulas_detected"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Extract per-sheet tables and workbook metadata from Excel files.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Process the Excel workbook and extract per-sheet data with "
            "headers and metadata. "
            "Include column_metadata, data_preview, detected_schema, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: sheets, column_metadata, data_preview, detected_schema, workbook_metadata, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
