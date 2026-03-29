from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import Any, Literal

from crewai import Agent, LLM

from core.config import settings
from services.agents import AGENT_MODULES, get_agent_module

ModelType = Literal[
    "heavy",
    "heavy_alt",
    "light",
    "gemini_api",
    "gemini_vision",
    "light_plus_scraper",
    "rule_plus_light",
    "hybrid",
    "system_service",
    "light_plus_pgvector",
    "elevenlabs_api",
]


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    model_type: ModelType
    input_description: str
    output_description: str
    responsibilities: str
    dependencies: list[str]
    implementation_notes: str
    priority: str


@dataclass
class AgentNode:
    spec: AgentSpec
    runtime_kind: str
    model_resolved: str
    dependencies_resolved: bool
    unresolved_dependencies: list[str]
    initialized: bool
    runtime_agent: Agent | None = None


def _normalize_model(model: str) -> str:
    normalized = model.strip()
    # LiteLLM/CrewAI requires an explicit provider prefix for custom model IDs.
    # We use Featherless via OpenAI-compatible API, so force OpenAI routing.
    if "/" in normalized and not normalized.startswith(("openai/", "azure/", "gemini/")):
        return f"openai/{normalized}"
    return normalized


def _prime_crewai_env() -> None:
    """CrewAI reads OPENAI_* env vars internally for its LLM wire protocol. We
    point them to Featherless (OpenAI-compatible base URL + API key)."""
    os.environ.setdefault("OPENAI_BASE_URL", settings.llm_base_url)
    os.environ.setdefault("OPENAI_API_KEY", settings.llm_api_key or "DATALYZE_PLACEHOLDER_KEY")


def _agent_specs() -> list[AgentSpec]:
    return [
        AgentSpec(
            id="orchestrator",
            name="Orchestrator Agent",
            model_type="heavy",
            input_description="Run context, onboarding config, agent statuses, failure telemetry",
            output_description="Ordered execution plan, next-agent dispatches, retries/fallback decisions",
            responsibilities="Global coordination, dependency enforcement, loop-back behavior, strategic recommendation orchestration",
            dependencies=[],
            implementation_notes="Stateful run controller; enforce max-retry and timeout windows",
            priority="Core",
        ),
        AgentSpec(
            id="pipeline_classifier",
            name="Pipeline Classifier Agent",
            model_type="gemini_api",
            input_description="Onboarding responses, company context, user-selected goals",
            output_description="Active track config + priority map + scraper targeting strategy",
            responsibilities="Choose one of four tracks; configure emphasis profile; vision support for PDFs/images",
            dependencies=["orchestrator"],
            implementation_notes="Deterministic JSON schema output; fallback to local rules if unavailable",
            priority="Core",
        ),
        AgentSpec(
            id="public_data_scraper",
            name="Public Data Scraper Agent",
            model_type="light_plus_scraper",
            input_description="Track profile, company context, admin play/pause state",
            output_description="Scraped artifacts, source metadata, credibility tags",
            responsibilities="Gather public evidence aligned to track objective",
            dependencies=["pipeline_classifier", "orchestrator"],
            implementation_notes="Single active company session; bounded crawl depth",
            priority="Core (for Public Mode)",
        ),
        AgentSpec(
            id="file_type_classifier",
            name="File Type Classifier Agent",
            model_type="light",
            input_description="Uploaded file manifest + mime hints",
            output_description="File type routing map + metadata tags",
            responsibilities="Correct processor dispatch",
            dependencies=["orchestrator"],
            implementation_notes="Include heuristic fallback by extension/mime",
            priority="Core",
        ),
        AgentSpec(
            id="pdf_processor",
            name="PDF Processor Agent",
            model_type="light",
            input_description="PDF bytes",
            output_description="Chunked text + table/chart extraction references",
            responsibilities="Parse PDFs, OCR via Gemini vision when needed",
            dependencies=["file_type_classifier"],
            implementation_notes="Track page-to-chunk mapping for provenance",
            priority="Core",
        ),
        AgentSpec(
            id="csv_processor",
            name="CSV Processor Agent",
            model_type="rule_plus_light",
            input_description="CSV files",
            output_description="Structured rows, inferred schema, summary stats",
            responsibilities="Parse and normalize tabular data",
            dependencies=["file_type_classifier"],
            implementation_notes="Detect delimiter/header anomalies",
            priority="Core",
        ),
        AgentSpec(
            id="excel_processor",
            name="Excel Processor Agent",
            model_type="rule_plus_light",
            input_description="XLS/XLSX files",
            output_description="Per-sheet extracted tables + workbook metadata",
            responsibilities="Handle multisheet extraction",
            dependencies=["file_type_classifier"],
            implementation_notes="Preserve sheet names and ranges",
            priority="Core",
        ),
        AgentSpec(
            id="json_processor",
            name="JSON Processor Agent",
            model_type="rule_plus_light",
            input_description="JSON documents",
            output_description="Flattened/normalized records + nested relation map",
            responsibilities="Extract nested structures to usable form",
            dependencies=["file_type_classifier"],
            implementation_notes="Keep parent-child path references",
            priority="Core",
        ),
        AgentSpec(
            id="image_multimodal_processor",
            name="Image/Multimodal Processor Agent",
            model_type="gemini_vision",
            input_description="Images, chart screenshots, whiteboard photos",
            output_description="Extracted text/labels/chart interpretations",
            responsibilities="Recover information from non-text uploads",
            dependencies=["file_type_classifier"],
            implementation_notes="Confidence threshold + manual review flag",
            priority="Core",
        ),
        AgentSpec(
            id="plain_text_processor",
            name="Plain Text Processor Agent",
            model_type="light",
            input_description="TXT/MD/log-like inputs",
            output_description="Clean chunks with semantic tags",
            responsibilities="Direct text extraction",
            dependencies=["file_type_classifier"],
            implementation_notes="Language detection optional",
            priority="Core",
        ),
        AgentSpec(
            id="data_cleaning",
            name="Data Cleaning Agent",
            model_type="light",
            input_description="Raw extracted chunks",
            output_description="Normalized chunks, dedup flags, standardized formats",
            responsibilities="Data hygiene before aggregation",
            dependencies=[
                "pdf_processor",
                "csv_processor",
                "excel_processor",
                "json_processor",
                "image_multimodal_processor",
                "plain_text_processor",
            ],
            implementation_notes="Date/number normalization and encoding cleanup",
            priority="Core",
        ),
        AgentSpec(
            id="smart_categorizer_metadata",
            name="Smart Categorizer / Metadata Agent",
            model_type="light",
            input_description="Cleaned chunks",
            output_description="Domain tags (finance/HR/ops/etc.), content-type tags",
            responsibilities="Improve aggregation and retrieval precision",
            dependencies=["data_cleaning"],
            implementation_notes="Multi-label tagging allowed",
            priority="Core",
        ),
        AgentSpec(
            id="aggregator",
            name="Aggregator Agent",
            model_type="heavy_alt",
            input_description="Cleaned + categorized chunks + scraper artifacts",
            output_description="Structured analysis corpus, usefulness scores, storyline hypotheses",
            responsibilities="Prioritize evidence and prepare synthesis-ready dataset",
            dependencies=["data_cleaning", "smart_categorizer_metadata", "public_data_scraper"],
            implementation_notes="Keep low-value data retained but deprioritized",
            priority="Core",
        ),
        AgentSpec(
            id="conflict_detection",
            name="Conflict Detection Agent",
            model_type="light",
            input_description="Aggregated corpus",
            output_description="Contradiction alerts with supporting references",
            responsibilities="Surface inconsistent records/statements",
            dependencies=["aggregator"],
            implementation_notes="Confidence + severity levels",
            priority="Core",
        ),
        AgentSpec(
            id="knowledge_graph_builder",
            name="Knowledge Graph Builder Agent",
            model_type="heavy_alt",
            input_description="Aggregated corpus and entity map",
            output_description="Nodes/edges for graph tables and UI rendering",
            responsibilities="Build entity relationship network",
            dependencies=["aggregator"],
            implementation_notes="Typed nodes/edges for rich filtering",
            priority="Core",
        ),
        AgentSpec(
            id="trend_forecasting",
            name="Trend Forecasting Agent",
            model_type="heavy_alt",
            input_description="Time-series candidates from aggregated corpus",
            output_description="Forecast values, confidence bands, plotting payloads",
            responsibilities="Predict KPI trajectories when enabled",
            dependencies=["aggregator"],
            implementation_notes="Strictly optional per run toggle",
            priority="Core (toggleable)",
        ),
        AgentSpec(
            id="sentiment_analysis",
            name="Sentiment Analysis Agent",
            model_type="light",
            input_description="Feedback/review/social text data",
            output_description="Sentiment labels, trend summaries, chart payloads",
            responsibilities="Customer sentiment interpretation",
            dependencies=["aggregator"],
            implementation_notes="Track source channel metadata",
            priority="Core",
        ),
        AgentSpec(
            id="insight_generation",
            name="Insight Generation Agent",
            model_type="heavy_alt",
            input_description="Aggregated evidence + conflict/sentiment/forecast signals",
            output_description="Insight cards with confidence and provenance tags",
            responsibilities="Primary business insight synthesis",
            dependencies=[
                "aggregator",
                "conflict_detection",
                "trend_forecasting",
                "sentiment_analysis",
            ],
            implementation_notes="Must output structured JSON for UI compatibility",
            priority="Core",
        ),
        AgentSpec(
            id="swot_analysis",
            name="SWOT Analysis Agent",
            model_type="heavy_alt",
            input_description="Insight set + aggregated corpus",
            output_description="Structured SWOT quadrants",
            responsibilities="Strategic framing",
            dependencies=["insight_generation", "aggregator"],
            implementation_notes="Ground each quadrant item in cited evidence",
            priority="Core",
        ),
        AgentSpec(
            id="executive_summary",
            name="Executive Summary Agent",
            model_type="heavy_alt",
            input_description="Finalized insight package + SWOT + risk/conflict highlights",
            output_description="Board-ready concise summary",
            responsibilities="Human-readable synthesis for decision-makers",
            # Do not depend on swot_analysis: it is optional on several tracks; skipped SWOT
            # must not block the board summary (or narration / title generation).
            dependencies=["insight_generation", "conflict_detection"],
            implementation_notes="Export-safe formatting",
            priority="Core",
        ),
        AgentSpec(
            id="automation_strategy",
            name="Automation Strategy Agent",
            model_type="hybrid",
            input_description="Aggregated operations/process evidence",
            output_description="2-3 step automation prototype suggestions",
            responsibilities="Recommend practical automation opportunities",
            dependencies=["aggregator", "pipeline_classifier"],
            implementation_notes="Suggestive only; no full auto-implementation",
            priority="Core",
        ),
        AgentSpec(
            id="data_provenance_tracker",
            name="Data Provenance Tracker",
            model_type="system_service",
            input_description="All transformations and source references",
            output_description="Source lineage links on every insight/output artifact",
            responsibilities="Explainability and auditability",
            dependencies=[],
            implementation_notes="Store lineage at chunk + insight levels",
            priority="Core",
        ),
        AgentSpec(
            id="natural_language_search",
            name="Natural Language Search Agent",
            model_type="light_plus_pgvector",
            input_description="User chat query + embedded corpus",
            output_description="Grounded answer + optional chart spec",
            responsibilities="Conversational analytics",
            dependencies=["data_cleaning", "smart_categorizer_metadata", "data_provenance_tracker"],
            implementation_notes="Retrieval-augmented answer policy with source citations",
            priority="Core",
        ),
        AgentSpec(
            id="elevenlabs_narration",
            name="ElevenLabs Narration Agent",
            model_type="elevenlabs_api",
            input_description="Executive summary text",
            output_description="MP3 narration asset",
            responsibilities="Audio delivery channel",
            dependencies=["executive_summary"],
            implementation_notes="Store and expose downloadable file URL",
            priority="Core (for ElevenLabs prize objective)",
        ),
    ]


class AgentRegistry:
    def __init__(self) -> None:
        self.specs = _agent_specs()
        self.specs_by_id = {spec.id: spec for spec in self.specs}
        self.nodes: dict[str, AgentNode] = {}
        self.booted_at: datetime | None = None
        self.errors: list[str] = []
        self._llm_cache: dict[str, LLM] = {}

    def _resolve_model(self, model_type: ModelType) -> str:
        if model_type == "heavy":
            return settings.heavy_model
        if model_type == "heavy_alt":
            return settings.heavy_alt_model
        if model_type in {"light", "light_plus_scraper", "rule_plus_light", "light_plus_pgvector"}:
            return settings.light_model
        if model_type == "hybrid":
            return f"{settings.light_model} (default) + {settings.heavy_alt_model} (escalation)"
        if model_type == "gemini_api":
            return settings.gemini_model
        if model_type == "gemini_vision":
            return settings.gemini_model
        if model_type == "elevenlabs_api":
            return "elevenlabs-api"
        return "system-service"

    def _runtime_kind(self, model_type: ModelType) -> str:
        if model_type in {
            "heavy",
            "heavy_alt",
            "light",
            "light_plus_scraper",
            "rule_plus_light",
            "hybrid",
            "light_plus_pgvector",
        }:
            return f"{settings.llm_provider}-crewai"
        if model_type in {"gemini_api", "gemini_vision", "elevenlabs_api"}:
            return "external-service"
        return "system-layer"

    def _get_llm(self, model_name: str) -> LLM:
        _prime_crewai_env()
        normalized = _normalize_model(model_name)
        if normalized not in self._llm_cache:
            self._llm_cache[normalized] = LLM(
                model=normalized,
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
            )
        return self._llm_cache[normalized]

    def _build_local_agent(self, spec: AgentSpec) -> Agent:
        if spec.model_type == "heavy":
            llm = self._get_llm(settings.heavy_model)
        elif spec.model_type == "heavy_alt":
            llm = self._get_llm(settings.heavy_alt_model)
        else:
            llm = self._get_llm(settings.light_model)

        agent_module = get_agent_module(spec.id)
        if agent_module is not None:
            return agent_module.build_agent(llm)

        return Agent(
            role=spec.name,
            goal=spec.responsibilities,
            backstory=spec.implementation_notes,
            llm=llm,
            verbose=False,
        )

    def initialize(self) -> None:
        self.errors = []
        self.nodes = {}

        known_ids = set(self.specs_by_id.keys())
        for spec in self.specs:
            missing = [dep for dep in spec.dependencies if dep not in known_ids]
            if missing:
                self.errors.append(
                    f"{spec.id} has unknown dependencies: {', '.join(missing)}",
                )

            runtime_kind = self._runtime_kind(spec.model_type)
            model_resolved = self._resolve_model(spec.model_type)
            unresolved = [dep for dep in spec.dependencies if dep not in self.specs_by_id]

            runtime_agent: Agent | None = None
            initialized = True

            if runtime_kind == f"{settings.llm_provider}-crewai" or runtime_kind == "local-crewai":
                try:
                    runtime_agent = self._build_local_agent(spec)
                except Exception as exc:
                    initialized = False
                    self.errors.append(f"{spec.id} init failed: {exc}")

            self.nodes[spec.id] = AgentNode(
                spec=spec,
                runtime_kind=runtime_kind,
                model_resolved=model_resolved,
                dependencies_resolved=len(unresolved) == 0,
                unresolved_dependencies=unresolved,
                initialized=initialized,
                runtime_agent=runtime_agent,
            )

        self.booted_at = datetime.now(UTC)

    def snapshot(self) -> dict[str, Any]:
        local_count = sum(
            1
            for node in self.nodes.values()
            if node.runtime_kind == f"{settings.llm_provider}-crewai"
            or node.runtime_kind == "local-crewai"
        )
        external_count = sum(1 for node in self.nodes.values() if node.runtime_kind == "external-service")
        system_count = sum(1 for node in self.nodes.values() if node.runtime_kind == "system-layer")
        initialized_count = sum(1 for node in self.nodes.values() if node.initialized)

        crewai_nodes = [
            n
            for n in self.nodes.values()
            if n.runtime_kind == f"{settings.llm_provider}-crewai"
            or n.runtime_kind == "local-crewai"
        ]
        crewai_total = len(crewai_nodes)
        crewai_initialized = sum(1 for n in crewai_nodes if n.initialized)
        init_summary = (
            f"{crewai_initialized}/{crewai_total} CrewAI LLM agents ready; "
            f"{initialized_count}/{len(self.nodes)} registry slots OK."
        )

        return {
            "status": (
                "ready"
                if initialized_count == len(self.nodes)
                and crewai_initialized == crewai_total
                and not self.errors
                else "degraded"
            ),
            "booted_at": self.booted_at.isoformat() if self.booted_at else None,
            "total_agents": len(self.nodes),
            "initialized_agents": initialized_count,
            "crewai_total": crewai_total,
            "crewai_initialized": crewai_initialized,
            "init_summary": init_summary,
            "local_agents": local_count,
            "external_agents": external_count,
            "system_agents": system_count,
            "errors": self.errors,
            "agents": [
                {
                    "id": node.spec.id,
                    "name": node.spec.name,
                    "model_type": node.spec.model_type,
                    "model_resolved": node.model_resolved,
                    "runtime_kind": node.runtime_kind,
                    "priority": node.spec.priority,
                    "responsibilities": node.spec.responsibilities,
                    "input_description": node.spec.input_description,
                    "output_description": node.spec.output_description,
                    "dependencies": node.spec.dependencies,
                    "dependencies_resolved": node.dependencies_resolved,
                    "unresolved_dependencies": node.unresolved_dependencies,
                    "implementation_notes": node.spec.implementation_notes,
                    "initialized": node.initialized,
                }
                for node in self.nodes.values()
            ],
            "orchestrator_policy": {
                "max_retries": settings.orchestrator_max_retries,
                "timeout_seconds": settings.orchestrator_timeout_seconds,
            },
        }


_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def boot_registry() -> dict[str, Any]:
    registry = get_registry()
    registry.initialize()
    return registry.snapshot()
