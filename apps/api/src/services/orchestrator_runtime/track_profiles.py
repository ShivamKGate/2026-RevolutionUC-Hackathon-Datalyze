"""
Track profile packs mapping onboarding paths to agent execution plans.

Track comes from onboarding_path / profile setting.
Track edits affect future runs only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from services.orchestrator_runtime.contracts import StageID


class TrackID(str, Enum):
    PREDICTIVE = "predictive"
    AUTOMATION = "automation"
    OPTIMIZATION = "optimization"
    SUPPLY_CHAIN = "supply_chain"


# Map user-facing onboarding_path values to canonical track IDs
ONBOARDING_PATH_TO_TRACK: dict[str, TrackID] = {
    "Deep Analysis": TrackID.PREDICTIVE,
    "deep_analysis": TrackID.PREDICTIVE,
    "predictive": TrackID.PREDICTIVE,
    "DevOps/Automations": TrackID.AUTOMATION,
    "devops_automations": TrackID.AUTOMATION,
    "automation": TrackID.AUTOMATION,
    "automations": TrackID.AUTOMATION,
    "devops": TrackID.AUTOMATION,
    "Business Automations": TrackID.OPTIMIZATION,
    "business_automations": TrackID.OPTIMIZATION,
    "optimization_track": TrackID.OPTIMIZATION,
    "optimization": TrackID.OPTIMIZATION,
    "supply chain": TrackID.SUPPLY_CHAIN,
    "supply_chain": TrackID.SUPPLY_CHAIN,
}

DEFAULT_TRACK = TrackID.PREDICTIVE


def resolve_track(onboarding_path: str | None) -> TrackID:
    if not onboarding_path:
        return DEFAULT_TRACK
    return ONBOARDING_PATH_TO_TRACK.get(onboarding_path.strip(), DEFAULT_TRACK)


@dataclass(frozen=True)
class StageConfig:
    stage_id: StageID
    agents: list[str]
    optional_agents: list[str] = field(default_factory=list)
    quality_gate: bool = True


@dataclass(frozen=True)
class TrackProfile:
    track_id: TrackID
    name: str
    description: str
    stages: list[StageConfig]
    focus_agents: list[str] = field(default_factory=list)

    def all_agent_ids(self) -> list[str]:
        out: list[str] = []
        for stage in self.stages:
            for a in stage.agents + stage.optional_agents:
                if a not in out:
                    out.append(a)
        return out


# Shared base stages used across tracks
_CLASSIFY_STAGE = StageConfig(
    stage_id=StageID.CLASSIFY,
    agents=["pipeline_classifier"],
    quality_gate=True,
)

_INGEST_STAGE = StageConfig(
    stage_id=StageID.INGEST,
    agents=["file_type_classifier", "pdf_processor", "csv_processor",
            "excel_processor", "json_processor", "plain_text_processor"],
    optional_agents=["image_multimodal_processor"],
    quality_gate=True,
)

_PROCESS_STAGE = StageConfig(
    stage_id=StageID.PROCESS,
    agents=["data_cleaning", "smart_categorizer_metadata"],
    quality_gate=True,
)

_FINALIZE_STAGE = StageConfig(
    stage_id=StageID.FINALIZE,
    agents=["executive_summary"],
    optional_agents=["elevenlabs_narration"],
    quality_gate=False,
)


TRACK_PROFILES: dict[TrackID, TrackProfile] = {
    TrackID.PREDICTIVE: TrackProfile(
        track_id=TrackID.PREDICTIVE,
        name="Predictive / Trend Forecasting",
        description="KPI projections, confidence bands, executive projections",
        focus_agents=["trend_forecasting", "insight_generation"],
        stages=[
            _CLASSIFY_STAGE,
            _INGEST_STAGE,
            _PROCESS_STAGE,
            StageConfig(
                stage_id=StageID.AGGREGATE,
                agents=["aggregator"],
                optional_agents=["public_data_scraper"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.ANALYZE,
                agents=["conflict_detection", "trend_forecasting",
                        "sentiment_analysis", "knowledge_graph_builder"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.SYNTHESIZE,
                agents=["insight_generation", "swot_analysis"],
                quality_gate=True,
            ),
            _FINALIZE_STAGE,
        ],
    ),
    TrackID.AUTOMATION: TrackProfile(
        track_id=TrackID.AUTOMATION,
        name="Automation Strategy",
        description="Process bottlenecks, automation opportunities, prototype steps",
        focus_agents=["automation_strategy", "insight_generation"],
        stages=[
            _CLASSIFY_STAGE,
            _INGEST_STAGE,
            _PROCESS_STAGE,
            StageConfig(
                stage_id=StageID.AGGREGATE,
                agents=["aggregator"],
                optional_agents=["public_data_scraper"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.ANALYZE,
                agents=["conflict_detection", "sentiment_analysis",
                        "knowledge_graph_builder"],
                optional_agents=["trend_forecasting"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.SYNTHESIZE,
                agents=["insight_generation", "automation_strategy", "swot_analysis"],
                quality_gate=True,
            ),
            _FINALIZE_STAGE,
        ],
    ),
    TrackID.OPTIMIZATION: TrackProfile(
        track_id=TrackID.OPTIMIZATION,
        name="Business Optimization",
        description="Operational inefficiency findings, strategic recommendations",
        focus_agents=["conflict_detection", "insight_generation", "swot_analysis"],
        stages=[
            _CLASSIFY_STAGE,
            _INGEST_STAGE,
            _PROCESS_STAGE,
            StageConfig(
                stage_id=StageID.AGGREGATE,
                agents=["aggregator"],
                optional_agents=["public_data_scraper"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.ANALYZE,
                agents=["conflict_detection", "sentiment_analysis",
                        "knowledge_graph_builder"],
                optional_agents=["trend_forecasting"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.SYNTHESIZE,
                agents=["insight_generation", "swot_analysis"],
                quality_gate=True,
            ),
            _FINALIZE_STAGE,
        ],
    ),
    TrackID.SUPPLY_CHAIN: TrackProfile(
        track_id=TrackID.SUPPLY_CHAIN,
        name="Supply Chain & Operations",
        description="Operational stability, delay/cost risk signals, resilience",
        focus_agents=["trend_forecasting", "conflict_detection", "insight_generation"],
        stages=[
            _CLASSIFY_STAGE,
            _INGEST_STAGE,
            _PROCESS_STAGE,
            StageConfig(
                stage_id=StageID.AGGREGATE,
                agents=["aggregator"],
                optional_agents=["public_data_scraper"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.ANALYZE,
                agents=["conflict_detection", "trend_forecasting",
                        "sentiment_analysis", "knowledge_graph_builder"],
                quality_gate=True,
            ),
            StageConfig(
                stage_id=StageID.SYNTHESIZE,
                agents=["insight_generation", "swot_analysis"],
                quality_gate=True,
            ),
            _FINALIZE_STAGE,
        ],
    ),
}


def get_track_profile(track_id: TrackID) -> TrackProfile:
    return TRACK_PROFILES[track_id]
