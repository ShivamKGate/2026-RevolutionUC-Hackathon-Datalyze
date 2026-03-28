from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from db.session import SessionLocal
from schemas.files_runs import PipelineRunOut, StartPipelineRunRequest
from services.agent_registry import get_registry

router = APIRouter()


def _require_company(user: dict) -> tuple[int, str]:
    cid = user.get("company_id")
    cname = user.get("company_name") or ""
    if cid is None:
        raise HTTPException(status_code=400, detail="User has no company assigned")
    if not cname.strip():
        cname = "company"
    return int(cid), cname.strip()


def _coerce_json_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _placeholder_logs(slug: str) -> list[str]:
    return [
        f"[{slug}] Pipeline started (placeholder run).",
        "[ingest] Context loaded; no live agent graph executed in this stub.",
        "[orchestrator] Placeholder dispatch recorded.",
        "[summary] Mock metrics: duration≈instant, artifacts=n/a.",
        f"[{slug}] Pipeline completed (placeholder).",
    ]


def _placeholder_agents() -> list[dict]:
    registry = get_registry()
    if not registry.nodes:
        registry.initialize()
    snap = registry.snapshot()
    out: list[dict] = []
    for node in snap.get("agents", [])[:14]:
        out.append(
            {
                "agent_id": node["id"],
                "agent_name": node["name"],
                "status": "completed",
                "message": f"Placeholder activity for {node['id']} (read-only registry snapshot).",
            },
        )
    return out


def _row_to_out(row) -> PipelineRunOut:
    sfi = row.source_file_ids
    if sfi is None:
        ids: list[int] = []
    elif isinstance(sfi, list):
        ids = [int(x) for x in sfi]
    else:
        ids = []
    return PipelineRunOut(
        id=row.id,
        slug=row.slug,
        status=row.status,
        started_at=row.started_at,
        ended_at=row.ended_at,
        summary=row.summary,
        pipeline_log=_coerce_json_list(row.pipeline_log),
        agent_activity=_coerce_json_list(row.agent_activity),
        source_file_ids=ids,
    )


def _validate_file_ids(db, company_id: int, file_ids: list[int]) -> None:
    if not file_ids:
        return
    uniq = sorted(set(int(x) for x in file_ids))
    if any(i <= 0 for i in uniq):
        raise HTTPException(status_code=400, detail="Invalid file id")
    in_clause = ",".join(str(i) for i in uniq)
    n = db.execute(
        text(f"SELECT COUNT(*) AS n FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause})"),
        {"cid": company_id},
    ).scalar()
    if int(n or 0) != len(uniq):
        raise HTTPException(status_code=400, detail="One or more file IDs are invalid")


@router.post("/start", response_model=PipelineRunOut)
def start_run(request: Request, body: StartPipelineRunRequest):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    user_id = int(user["id"])
    scrape = bool(user.get("public_scrape_enabled"))

    file_ids = [int(x) for x in body.uploaded_file_ids]

    if not file_ids and not scrape:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one file or enable “Transcrape public data” in Company settings to start without uploads.",
        )

    db = SessionLocal()
    try:
        _validate_file_ids(db, company_id, file_ids)

        slug = secrets.token_urlsafe(12).replace("-", "_")[:32]
        logs = _placeholder_logs(slug)
        agents = _placeholder_agents()
        now = datetime.now(UTC)
        summary = (
            f"Placeholder run finished. Files: {len(file_ids)}. "
            f"Public scrape mode: {scrape}."
        )

        row = db.execute(
            text(
                "INSERT INTO pipeline_runs (slug, company_id, user_id, status, started_at, ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids) "
                "VALUES (:slug, :cid, :uid, 'completed', :st, :en, :summary, CAST(:log AS jsonb), "
                "CAST(:agents AS jsonb), :fids) "
                "RETURNING id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids"
            ),
            {
                "slug": slug,
                "cid": company_id,
                "uid": user_id,
                "st": now,
                "en": now,
                "summary": summary,
                "log": json.dumps(logs),
                "agents": json.dumps(agents),
                "fids": file_ids,
            },
        ).fetchone()
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return _row_to_out(row)


@router.get("", response_model=list[PipelineRunOut])
def list_runs(request: Request):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids "
                "FROM pipeline_runs WHERE company_id=:cid ORDER BY started_at DESC LIMIT 100"
            ),
            {"cid": company_id},
        ).fetchall()
    finally:
        db.close()
    return [_row_to_out(r) for r in rows]


@router.get("/latest/summary", response_model=PipelineRunOut | None)
def latest_run(request: Request):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids "
                "FROM pipeline_runs WHERE company_id=:cid ORDER BY started_at DESC LIMIT 1"
            ),
            {"cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        return None
    return _row_to_out(row)


@router.get("/{slug}", response_model=PipelineRunOut)
def get_run(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids "
                "FROM pipeline_runs WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_out(row)
