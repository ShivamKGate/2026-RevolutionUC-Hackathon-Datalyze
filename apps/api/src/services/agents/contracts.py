"""
Per-agent output contracts: JSON schemas, strictness profiles, and
adapter-envelope mapping.

The AGENT_CONTRACTS dict is the single source of truth for:
  - required output keys per agent
  - optional output keys
  - strictness mode (strict | guarded)
  - token budget guidance
  - scope boundary description

The ADAPTER_ENVELOPE_SCHEMA defines the orchestrator integration seam.
"""

from __future__ import annotations

from typing import Any

ADAPTER_ENVELOPE_SCHEMA: dict[str, Any] = {
    "status": "ok|warning|error",
    "summary": "string",
    "artifacts": [],
    "next_hints": [],
    "confidence": 0.0,
    "errors": [],
}

ADAPTER_ENVELOPE_REQUIRED_KEYS = {"status", "summary", "artifacts", "next_hints", "confidence", "errors"}


class AgentContract:
    __slots__ = (
        "agent_id", "required_keys", "optional_keys", "strictness",
        "token_budget", "scope_boundary",
    )

    def __init__(
        self,
        agent_id: str,
        required_keys: list[str],
        optional_keys: list[str] | None = None,
        strictness: str = "strict",
        token_budget: int = 800,
        scope_boundary: str = "",
    ) -> None:
        self.agent_id = agent_id
        self.required_keys = required_keys
        self.optional_keys = optional_keys or []
        self.strictness = strictness
        self.token_budget = token_budget
        self.scope_boundary = scope_boundary

    def validate_output(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for key in self.required_keys:
            if key not in output:
                errors.append(f"Missing required key: {key}")
        return len(errors) == 0, errors


AGENT_CONTRACTS: dict[str, AgentContract] = {
    "pipeline_classifier": AgentContract(
        agent_id="pipeline_classifier",
        required_keys=["track", "priority_map", "scraper_strategy"],
        optional_keys=["vision_fallback", "confidence"],
        strictness="strict",
        token_budget=600,
        scope_boundary="track classification and priority mapping only",
    ),
    "public_data_scraper": AgentContract(
        agent_id="public_data_scraper",
        required_keys=["artifacts", "sources", "credibility_tags"],
        optional_keys=["crawl_depth", "warnings"],
        strictness="strict",
        token_budget=1000,
        scope_boundary="public data gathering and source tagging only",
    ),
    "file_type_classifier": AgentContract(
        agent_id="file_type_classifier",
        required_keys=["file_routing", "metadata_tags"],
        optional_keys=["heuristic_fallbacks"],
        strictness="strict",
        token_budget=400,
        scope_boundary="file type detection and routing only",
    ),
    "pdf_processor": AgentContract(
        agent_id="pdf_processor",
        required_keys=["chunks", "page_map"],
        optional_keys=["tables", "charts", "ocr_used"],
        strictness="strict",
        token_budget=800,
        scope_boundary="PDF parsing and text extraction only",
    ),
    "csv_processor": AgentContract(
        agent_id="csv_processor",
        required_keys=["rows_summary", "inferred_schema", "stats"],
        optional_keys=["delimiter", "header_anomalies", "encoding"],
        strictness="strict",
        token_budget=600,
        scope_boundary="CSV parsing and schema inference only",
    ),
    "excel_processor": AgentContract(
        agent_id="excel_processor",
        required_keys=["sheets", "workbook_metadata"],
        optional_keys=["named_ranges", "formulas_detected"],
        strictness="strict",
        token_budget=800,
        scope_boundary="Excel sheet extraction and metadata only",
    ),
    "json_processor": AgentContract(
        agent_id="json_processor",
        required_keys=["records", "nested_map"],
        optional_keys=["array_lengths", "depth"],
        strictness="strict",
        token_budget=600,
        scope_boundary="JSON flattening and structure mapping only",
    ),
    "image_multimodal_processor": AgentContract(
        agent_id="image_multimodal_processor",
        required_keys=["extracted_text", "labels", "interpretation"],
        optional_keys=["confidence", "manual_review_flag"],
        strictness="strict",
        token_budget=800,
        scope_boundary="image/chart text and label extraction only",
    ),
    "plain_text_processor": AgentContract(
        agent_id="plain_text_processor",
        required_keys=["chunks", "semantic_tags"],
        optional_keys=["language_detected", "line_count"],
        strictness="strict",
        token_budget=500,
        scope_boundary="plain text chunking and tagging only",
    ),
    "data_cleaning": AgentContract(
        agent_id="data_cleaning",
        required_keys=["cleaned_chunks", "dedup_flags", "normalization_applied"],
        optional_keys=["encoding_fixes", "format_corrections"],
        strictness="strict",
        token_budget=600,
        scope_boundary="data normalization and deduplication only",
    ),
    "smart_categorizer_metadata": AgentContract(
        agent_id="smart_categorizer_metadata",
        required_keys=["domain_tags", "content_type_tags"],
        optional_keys=["multi_label_map", "tag_confidence"],
        strictness="strict",
        token_budget=500,
        scope_boundary="domain categorization and metadata tagging only",
    ),
    "aggregator": AgentContract(
        agent_id="aggregator",
        required_keys=["corpus", "usefulness_scores", "storyline_hypotheses"],
        optional_keys=["low_value_retained", "source_distribution"],
        strictness="guarded",
        token_budget=1200,
        scope_boundary="evidence aggregation and prioritization",
    ),
    "conflict_detection": AgentContract(
        agent_id="conflict_detection",
        required_keys=["contradictions", "supporting_references"],
        optional_keys=["severity_levels", "confidence"],
        strictness="strict",
        token_budget=600,
        scope_boundary="contradiction and conflict detection only",
    ),
    "knowledge_graph_builder": AgentContract(
        agent_id="knowledge_graph_builder",
        required_keys=["nodes", "edges"],
        optional_keys=["node_types", "edge_types", "clusters"],
        strictness="guarded",
        token_budget=1200,
        scope_boundary="entity relationship graph construction",
    ),
    "trend_forecasting": AgentContract(
        agent_id="trend_forecasting",
        required_keys=["forecasts", "confidence_bands"],
        optional_keys=["plot_payloads", "methodology", "data_points_used"],
        strictness="guarded",
        token_budget=800,
        scope_boundary="time-series trend analysis and forecasting",
    ),
    "sentiment_analysis": AgentContract(
        agent_id="sentiment_analysis",
        required_keys=["sentiments", "trend_summary"],
        optional_keys=["chart_payloads", "source_channels", "sample_quotes"],
        strictness="strict",
        token_budget=600,
        scope_boundary="sentiment classification and trend summarization only",
    ),
    "insight_generation": AgentContract(
        agent_id="insight_generation",
        required_keys=["insights"],
        optional_keys=["provenance_tags", "confidence_scores", "impact_rankings"],
        strictness="guarded",
        token_budget=1000,
        scope_boundary="business insight synthesis from aggregated evidence",
    ),
    "swot_analysis": AgentContract(
        agent_id="swot_analysis",
        required_keys=["strengths", "weaknesses", "opportunities", "threats"],
        optional_keys=["evidence_citations", "priority_scores"],
        strictness="guarded",
        token_budget=1000,
        scope_boundary="SWOT quadrant analysis grounded in evidence",
    ),
    "executive_summary": AgentContract(
        agent_id="executive_summary",
        required_keys=["summary", "key_findings", "next_actions"],
        optional_keys=["risk_highlights", "confidence_statement"],
        strictness="guarded",
        token_budget=800,
        scope_boundary="board-ready executive summary synthesis",
    ),
    "automation_strategy": AgentContract(
        agent_id="automation_strategy",
        required_keys=["suggestions"],
        optional_keys=["feasibility_scores", "implementation_steps", "prerequisites"],
        strictness="guarded",
        token_budget=800,
        scope_boundary="automation opportunity recommendation",
    ),
    "natural_language_search": AgentContract(
        agent_id="natural_language_search",
        required_keys=["answer", "sources"],
        optional_keys=["chart_spec", "follow_up_suggestions"],
        strictness="strict",
        token_budget=600,
        scope_boundary="retrieval-augmented search and citation only",
    ),
    "elevenlabs_narration": AgentContract(
        agent_id="elevenlabs_narration",
        required_keys=["narration_text", "status"],
        optional_keys=["audio_url", "duration_estimate"],
        strictness="guarded",
        token_budget=400,
        scope_boundary="executive summary narration preparation",
    ),
}


def get_contract(agent_id: str) -> AgentContract | None:
    return AGENT_CONTRACTS.get(agent_id)


def get_all_in_scope_agent_ids() -> list[str]:
    return list(AGENT_CONTRACTS.keys())
