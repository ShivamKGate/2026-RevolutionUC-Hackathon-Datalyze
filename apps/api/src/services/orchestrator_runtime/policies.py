"""
Execution policies: retry, time budget, adaptive overrides, quality gates.

Implements the hybrid execution model:
  - deterministic DAG baseline
  - adaptive policy overrides (when enabled)
  - stage-gated quality checks (when enabled)
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from core.config import settings
from services.orchestrator_runtime.contracts import (
    AgentEnvelope,
    MemoryState,
    StageGateResult,
    StageID,
)


@dataclass
class RetryDecision:
    should_retry: bool
    reason: str
    attempt: int
    delay_seconds: float = 0.0


def evaluate_retry(
    agent_id: str,
    envelope: AgentEnvelope,
    memory: MemoryState,
    max_retries: int | None = None,
) -> RetryDecision:
    """Decide whether to retry a failed agent dispatch."""
    max_r = max_retries if max_retries is not None else settings.orchestrator_max_retries
    current_retries = memory.retries.get(agent_id, 0)

    if envelope.status != "error":
        return RetryDecision(should_retry=False, reason="not an error", attempt=current_retries)

    if current_retries >= max_r:
        return RetryDecision(
            should_retry=False,
            reason=f"max retries ({max_r}) exhausted",
            attempt=current_retries,
        )

    # Exponential backoff: 2^attempt seconds, capped at 30s
    delay = min(2 ** current_retries, 30)
    return RetryDecision(
        should_retry=True,
        reason=f"retry {current_retries + 1}/{max_r}",
        attempt=current_retries + 1,
        delay_seconds=delay,
    )


def check_time_budget(start_time: float, max_seconds: int | None = None) -> dict[str, Any]:
    """Check remaining time budget for the run."""
    max_s = max_seconds if max_seconds is not None else settings.orch_max_run_seconds
    elapsed = time.time() - start_time
    remaining = max(0, max_s - elapsed)
    return {
        "elapsed_seconds": round(elapsed, 1),
        "max_seconds": max_s,
        "remaining_seconds": round(remaining, 1),
        "budget_exceeded": remaining <= 0,
    }


def is_agent_ready(
    agent_id: str,
    completed_agents: list[str],
    agent_dependencies: dict[str, list[str]],
) -> bool:
    """Check if all dependencies for an agent are completed."""
    deps = agent_dependencies.get(agent_id, [])
    return all(d in completed_agents for d in deps)


def pick_next_agents(
    stage_agents: list[str],
    completed: list[str],
    failed: list[str],
    skipped: list[str],
    agent_dependencies: dict[str, list[str]],
    parallel_enabled: bool = False,
    adaptive_enabled: bool = False,
    focus_agents: list[str] | None = None,
    retries: dict[str, int] | None = None,
) -> list[str]:
    """Pick the next agent(s) to dispatch based on DAG readiness.

    If parallel_enabled, returns all ready agents. Otherwise returns
    the first ready agent only (sequential mode).
    """
    done_set = set(completed) | set(failed) | set(skipped)
    candidates = [a for a in stage_agents if a not in done_set]

    ready = [a for a in candidates if is_agent_ready(a, completed, agent_dependencies)]

    if not ready:
        return []
    if adaptive_enabled:
        focus_set = set(focus_agents or [])
        retry_map = retries or {}
        # Adaptive ordering override:
        # prioritize track focus agents and de-prioritize unstable/retried nodes.
        ready = sorted(
            ready,
            key=lambda a: (
                -(2 if a in focus_set else 0) + retry_map.get(a, 0),
                stage_agents.index(a),
            ),
        )
    if parallel_enabled:
        return ready
    return [ready[0]]


def evaluate_stage_gate(
    stage_id: StageID,
    memory: MemoryState,
    stage_agents: list[str],
    optional_agents: list[str] | None = None,
    prior_outputs: dict[str, dict[str, Any]] | None = None,
) -> StageGateResult:
    """Evaluate quality gate for a completed stage."""
    if not settings.orch_enable_stage_gates:
        return StageGateResult(passed=True, stage=stage_id.value)

    optional = set(optional_agents or [])
    required = [a for a in stage_agents if a not in optional]
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    # Check that all required agents completed
    for agent_id in required:
        completed = agent_id in memory.completed
        checks.append({
            "check": f"{agent_id}_completed",
            "passed": completed,
        })
        if not completed and agent_id not in memory.skipped:
            issues.append(f"Required agent {agent_id} did not complete")

    # Check that no required agent is in failed state
    for agent_id in required:
        if agent_id in memory.failed:
            issues.append(f"Required agent {agent_id} failed")

    # Quality checks on required agent outputs.
    outputs = prior_outputs or {}
    for agent_id in required:
        out = outputs.get(agent_id, {})
        summary = str(out.get("summary", "")).strip()
        confidence = float(out.get("confidence", 0.0))
        has_non_empty_summary = bool(summary)
        confidence_ok = confidence >= 0.35
        checks.append({"check": f"{agent_id}_summary_non_empty", "passed": has_non_empty_summary})
        checks.append({"check": f"{agent_id}_confidence_min", "passed": confidence_ok})
        if agent_id in memory.completed and not has_non_empty_summary:
            issues.append(f"Required agent {agent_id} returned empty summary")
        if agent_id in memory.completed and not confidence_ok:
            issues.append(f"Required agent {agent_id} confidence below threshold")

    passed = len(issues) == 0
    return StageGateResult(
        passed=passed,
        stage=stage_id.value,
        checks=checks,
        issues=issues,
    )


def classify_completion(memory: MemoryState) -> str:
    """Classify the final run status."""
    if memory.failed and not memory.completed:
        return "failed"
    if memory.warnings or memory.failed:
        return "completed_with_warnings"
    return "completed"


def generate_fix_suggestions(memory: MemoryState) -> list[str]:
    """Generate actionable fix suggestions for warnings/failures."""
    suggestions: list[str] = []
    for agent_id in memory.failed:
        retries = memory.retries.get(agent_id, 0)
        suggestions.append(
            f"Agent '{agent_id}' failed after {retries} retries. "
            f"Check model availability and input data quality."
        )
    if memory.timing_budget.get("budget_exceeded"):
        suggestions.append(
            "Run exceeded time budget. Consider reducing input size "
            "or increasing ORCH_MAX_RUN_SECONDS."
        )
    return suggestions
