"""File Type Classifier Agent — strict, light."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "file_type_classifier"
AGENT_NAME = "File Type Classifier Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 400

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="file type detection and routing only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You classify uploaded files by type and determine which processor agent "
        "should handle each file.\n\n"
        "Given a file manifest with filenames, MIME types, and size hints, produce "
        "a routing map that assigns each file to the correct processor.\n\n"
        "Supported processors: pdf_processor, csv_processor, excel_processor, "
        "json_processor, image_multimodal_processor, plain_text_processor.\n\n"
        "Output schema:\n"
        "{\n"
        '  "file_routing": [{"filename": "...", "detected_type": "pdf|csv|excel|json|image|text", '
        '"processor": "<processor_agent_id>", "confidence": 0.0-1.0}],\n'
        '  "metadata_tags": {"total_files": N, "types_detected": ["pdf", "csv", ...]}\n'
        "}\n\n"
        "Apply heuristic fallback by extension/MIME when content inspection is unavailable."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["file_routing", "metadata_tags"],
    "optional": ["heuristic_fallbacks"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Correctly classify files and route to appropriate processor agents.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Given the uploaded file manifest, classify each file by type and "
            "assign it to the correct processor agent. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: file_routing, metadata_tags',
        agent=agent,
        context=context_tasks or [],
    )
