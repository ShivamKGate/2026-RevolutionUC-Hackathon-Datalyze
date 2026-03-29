"""
Persistence layer: filesystem artifacts and DB log/replay projection.

Data authority model:
  - During execution: filesystem is source-of-truth for runtime state.
  - For UI/live + replay: DB is source-of-truth for display surfaces.

Strategy: write log/event rows to DB incrementally for live feed;
keep full heavy runtime internals in filesystem; on completion,
persist UI projection to DB for replay.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

from db.session import SessionLocal
from services.orchestrator_runtime.contracts import (
    AgentEnvelope,
    DecisionRecord,
    MemoryState,
    RunManifest,
    StageGateResult,
)


# ---------- Filesystem persistence ----------

def write_manifest(run_dir: Path, manifest: RunManifest) -> None:
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2), encoding="utf-8",
    )


def write_memory(run_dir: Path, memory: MemoryState) -> None:
    (run_dir / "memory.json").write_text(
        json.dumps(memory.to_dict(), indent=2), encoding="utf-8",
    )


def append_decision(run_dir: Path, record: DecisionRecord) -> None:
    with open(run_dir / "decision_ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record.to_dict()) + "\n")


def write_context_index(run_dir: Path, context_meta: dict[str, Any]) -> None:
    (run_dir / "context" / "context.json").write_text(
        json.dumps(context_meta, indent=2), encoding="utf-8",
    )


def write_agent_output(
    run_dir: Path,
    agent_id: str,
    step: int,
    envelope: AgentEnvelope,
) -> None:
    agent_dir = run_dir / "context" / "agent_outputs" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / f"step_{step}.json").write_text(
        json.dumps(envelope.to_dict(), indent=2), encoding="utf-8",
    )


def write_quality_gate(run_dir: Path, gate: StageGateResult) -> None:
    gate_dir = run_dir / "context" / "quality_gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / f"{gate.stage}_gate.json").write_text(
        json.dumps(gate.to_dict(), indent=2), encoding="utf-8",
    )


def update_artifacts_index(run_dir: Path, artifacts: list[dict[str, Any]]) -> None:
    idx_path = run_dir / "artifacts" / "index.json"
    existing: list[dict[str, Any]] = []
    if idx_path.exists():
        try:
            existing = json.loads(idx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    existing.extend(artifacts)
    idx_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def write_final_report(run_dir: Path, report: dict[str, Any]) -> None:
    (run_dir / "final_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8",
    )


def write_input_metadata(run_dir: Path, inputs: dict[str, Any]) -> None:
    (run_dir / "context" / "inputs" / "input_manifest.json").write_text(
        json.dumps(inputs, indent=2), encoding="utf-8",
    )


# ---------- Database persistence ----------

def db_insert_run_log(
    run_id: int,
    stage: str,
    agent: str,
    action: str,
    detail: str,
    status: str,
    meta: dict[str, Any] | None = None,
) -> None:
    """Insert a single log row for live feed / replay."""
    db = SessionLocal()
    try:
        db.execute(
            text(
                "INSERT INTO pipeline_run_logs "
                "(run_id, timestamp, stage, agent, action, detail, status, meta_json) "
                "VALUES (:rid, :ts, :stage, :agent, :action, :detail, :status, CAST(:meta AS jsonb))"
            ),
            {
                "rid": run_id,
                "ts": datetime.now(UTC),
                "stage": stage,
                "agent": agent,
                "action": action,
                "detail": detail[:2000] if detail else "",
                "status": status,
                "meta": json.dumps(meta or {}),
            },
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def db_update_run_status(
    run_id: int,
    status: str,
    summary: str | None = None,
    pipeline_log: list | None = None,
    agent_activity: list | None = None,
    track: str | None = None,
    config_json: dict | None = None,
    replay_payload: dict | None = None,
    run_dir_path: str | None = None,
) -> None:
    """Update pipeline_runs row with current status and optional projections."""
    db = SessionLocal()
    try:
        sets = ["status = :status"]
        params: dict[str, Any] = {"rid": run_id, "status": status}

        if summary is not None:
            sets.append("summary = :summary")
            params["summary"] = summary
        if pipeline_log is not None:
            sets.append("pipeline_log = CAST(:plog AS jsonb)")
            params["plog"] = json.dumps(pipeline_log)
        if agent_activity is not None:
            sets.append("agent_activity = CAST(:aact AS jsonb)")
            params["aact"] = json.dumps(agent_activity)
        if track is not None:
            sets.append("track = :track")
            params["track"] = track
        if config_json is not None:
            sets.append("config_json = CAST(:cfg AS jsonb)")
            params["cfg"] = json.dumps(config_json)
        if replay_payload is not None:
            sets.append("replay_payload = CAST(:rp AS jsonb)")
            params["rp"] = json.dumps(replay_payload)
        if run_dir_path is not None:
            sets.append("run_dir_path = :rdp")
            params["rdp"] = run_dir_path

        if status in ("completed", "completed_with_warnings", "failed"):
            sets.append("ended_at = NOW()")

        sql = f"UPDATE pipeline_runs SET {', '.join(sets)} WHERE id = :rid"
        db.execute(text(sql), params)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def db_get_run_logs(run_id: int) -> list[dict[str, Any]]:
    """Fetch all log entries for a run (for replay)."""
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT id, timestamp, stage, agent, action, detail, status, meta_json "
                "FROM pipeline_run_logs WHERE run_id = :rid ORDER BY timestamp ASC"
            ),
            {"rid": run_id},
        ).fetchall()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "stage": r.stage,
                "agent": r.agent,
                "action": r.action,
                "detail": r.detail,
                "status": r.status,
                "meta": r.meta_json if isinstance(r.meta_json, dict) else {},
            }
            for r in rows
        ]
    finally:
        db.close()


def db_insert_artifacts(
    run_id: int,
    agent_id: str,
    artifacts: list[dict[str, Any]],
) -> None:
    """Persist lightweight artifact references for UI queries."""
    if not artifacts:
        return
    db = SessionLocal()
    try:
        for artifact in artifacts:
            db.execute(
                text(
                    "INSERT INTO pipeline_run_artifacts "
                    "(run_id, agent_id, artifact_type, artifact_path, meta_json) "
                    "VALUES (:rid, :aid, :atype, :apath, CAST(:meta AS jsonb))"
                ),
                {
                    "rid": run_id,
                    "aid": agent_id,
                    "atype": str(artifact.get("type", "output"))[:60],
                    "apath": artifact.get("path"),
                    "meta": json.dumps(artifact),
                },
            )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
