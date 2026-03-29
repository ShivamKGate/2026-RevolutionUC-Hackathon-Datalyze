"""PDF Processor Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "pdf_processor"
AGENT_NAME = "PDF Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="PDF parsing and text extraction only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You parse PDF documents and extract structured text content.\n\n"
        "Break the document into semantic chunks preserving page boundaries. "
        "Extract tables and chart references where detectable.\n\n"
        "Output schema (keep compact, max 3 sample chunks):\n"
        "{\n"
        '  "chunks": [{"chunk_id": "c1", "page": 1, "content": "...", "type": "text"}],\n'
        '  "column_metadata": [],\n'
        '  "data_preview": {"sample_chunks": [{"chunk_id": "c1", "page": 1, "content": "..."}]},\n'
        '  "detected_schema": {"sections": ["financial_summary", "operations"], "tables_detected": N},\n'
        '  "page_map": {"total_pages": 1, "chunks_per_page": {"1": 1}},\n'
        '  "chart_suggestions": ["kpi_card", "section_bar_chart"]\n'
        "}\n\n"
        "Keep chunk content brief. Focus on structure over verbosity."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["chunks", "column_metadata", "data_preview", "detected_schema", "page_map", "chart_suggestions"],
    "optional": ["tables", "charts", "ocr_used"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Parse PDFs into structured, page-mapped text chunks.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Parse the provided PDF document into semantic chunks with page mapping. "
            "Extract tables and chart references if present. "
            "Include data_preview, detected_schema, and chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: chunks, column_metadata, data_preview, detected_schema, page_map, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
