"""
Per-agent specialization module index.

Import all agent builders via this package for registry and runtime consumption.
Each module exposes: AGENT_ID, AGENT_NAME, STRICTNESS, TOKEN_BUDGET,
SYSTEM_PROMPT, OUTPUT_SCHEMA, build_agent(llm), build_task(agent, context_tasks).

Model assignment is NOT in these modules — it stays in agent_registry.py.
"""

from __future__ import annotations

from typing import Any

from services.agents import (
    aggregator,
    automation_strategy,
    conflict_detection,
    csv_processor,
    data_cleaning,
    elevenlabs_narration,
    excel_processor,
    executive_summary,
    file_type_classifier,
    image_multimodal_processor,
    insight_generation,
    json_processor,
    knowledge_graph_builder,
    natural_language_search,
    pdf_processor,
    pipeline_classifier,
    plain_text_processor,
    public_data_scraper,
    sentiment_analysis,
    smart_categorizer_metadata,
    swot_analysis,
    trend_forecasting,
)

AGENT_MODULES: dict[str, Any] = {
    "pipeline_classifier": pipeline_classifier,
    "public_data_scraper": public_data_scraper,
    "file_type_classifier": file_type_classifier,
    "pdf_processor": pdf_processor,
    "csv_processor": csv_processor,
    "excel_processor": excel_processor,
    "json_processor": json_processor,
    "image_multimodal_processor": image_multimodal_processor,
    "plain_text_processor": plain_text_processor,
    "data_cleaning": data_cleaning,
    "smart_categorizer_metadata": smart_categorizer_metadata,
    "aggregator": aggregator,
    "conflict_detection": conflict_detection,
    "knowledge_graph_builder": knowledge_graph_builder,
    "trend_forecasting": trend_forecasting,
    "sentiment_analysis": sentiment_analysis,
    "insight_generation": insight_generation,
    "swot_analysis": swot_analysis,
    "executive_summary": executive_summary,
    "automation_strategy": automation_strategy,
    "natural_language_search": natural_language_search,
    "elevenlabs_narration": elevenlabs_narration,
}


def get_agent_module(agent_id: str) -> Any | None:
    return AGENT_MODULES.get(agent_id)


def get_all_agent_ids() -> list[str]:
    return list(AGENT_MODULES.keys())


def get_agent_system_prompt(agent_id: str) -> str | None:
    mod = AGENT_MODULES.get(agent_id)
    return getattr(mod, "SYSTEM_PROMPT", None) if mod else None


def get_agent_output_schema(agent_id: str) -> dict[str, Any] | None:
    mod = AGENT_MODULES.get(agent_id)
    return getattr(mod, "OUTPUT_SCHEMA", None) if mod else None
