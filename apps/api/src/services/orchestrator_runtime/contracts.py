"""
Adapter contracts and data structures for the orchestrator runtime.

This is the integration seam between orchestrator (Kartavya) and
agent specialization (Shivam). Both branches must honor these types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class StageID(str, Enum):
    CLASSIFY = "classify"
    INGEST = "ingest"
    PROCESS = "process"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    FINALIZE = "finalize"


@dataclass
class AgentEnvelope:
    """Normalized output contract for every agent dispatch.

    Specialization modules emit per-agent JSON; the adapter normalizes
    into this envelope so the orchestrator never parses raw model text.
    """
    status: str = "ok"  # ok | warning | error
    summary: str = ""
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    next_hints: list[str] = field(default_factory=list)
    confidence: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "artifacts": self.artifacts,
            "next_hints": self.next_hints,
            "confidence": self.confidence,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentEnvelope:
        return cls(
            status=d.get("status", "ok"),
            summary=d.get("summary", ""),
            artifacts=d.get("artifacts", []),
            next_hints=d.get("next_hints", []),
            confidence=float(d.get("confidence", 0.0)),
            errors=d.get("errors", []),
        )

    @classmethod
    def error_envelope(cls, msg: str) -> AgentEnvelope:
        return cls(status="error", summary=msg, errors=[msg], confidence=0.0)

    @classmethod
    def warning_envelope(cls, msg: str) -> AgentEnvelope:
        return cls(status="warning", summary=msg, confidence=0.3)


@dataclass
class DecisionRecord:
    """One row in decision_ledger.jsonl."""
    timestamp: str
    step: int
    stage: str
    agent_id: str
    why_this_agent: str
    alternatives_considered: list[str]
    policy_mode: str  # deterministic | adaptive
    confidence: float
    outcome: str  # dispatched | skipped | failed | retried

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "step": self.step,
            "stage": self.stage,
            "agent_id": self.agent_id,
            "why_this_agent": self.why_this_agent,
            "alternatives_considered": self.alternatives_considered,
            "policy_mode": self.policy_mode,
            "confidence": self.confidence,
            "outcome": self.outcome,
        }


@dataclass
class RunManifest:
    """Static run metadata written once at run start."""
    run_slug: str
    track: str
    company_id: int
    company_name: str
    user_id: int
    source_file_ids: list[int]
    public_scrape_enabled: bool
    parallel_enabled: bool
    adaptive_policy_enabled: bool
    stage_gates_enabled: bool
    max_run_seconds: int
    created_at: str
    model_config: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_slug": self.run_slug,
            "track": self.track,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "user_id": self.user_id,
            "source_file_ids": self.source_file_ids,
            "public_scrape_enabled": self.public_scrape_enabled,
            "parallel_enabled": self.parallel_enabled,
            "adaptive_policy_enabled": self.adaptive_policy_enabled,
            "stage_gates_enabled": self.stage_gates_enabled,
            "max_run_seconds": self.max_run_seconds,
            "created_at": self.created_at,
            "model_config": self.model_config,
        }


@dataclass
class MemoryState:
    """Mutable runtime state persisted to memory.json every step."""
    state: str = "running"
    current_stage: str = ""
    current_agent: str = ""
    step_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    retries: dict[str, int] = field(default_factory=dict)
    next_candidates: list[str] = field(default_factory=list)
    timing_budget: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fix_suggestions: list[str] = field(default_factory=list)
    done: bool = False

    def add_event(self, event_type: str, agent: str, detail: str = "") -> None:
        self.events.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "type": event_type,
            "agent": agent,
            "detail": detail,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "current_stage": self.current_stage,
            "current_agent": self.current_agent,
            "step_count": self.step_count,
            "events": self.events,
            "completed": self.completed,
            "pending": self.pending,
            "failed": self.failed,
            "skipped": self.skipped,
            "retries": self.retries,
            "next_candidates": self.next_candidates,
            "timing_budget": self.timing_budget,
            "warnings": self.warnings,
            "fix_suggestions": self.fix_suggestions,
            "done": self.done,
        }


@dataclass
class StageGateResult:
    """Result of a quality gate check between stages."""
    passed: bool
    stage: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "stage": self.stage,
            "checks": self.checks,
            "issues": self.issues,
        }
