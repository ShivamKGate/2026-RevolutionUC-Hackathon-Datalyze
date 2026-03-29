from __future__ import annotations

import json
import logging
import secrets
import shutil
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from db.session import SessionLocal
from schemas.files_runs import PipelineRunLogOut, PipelineRunOut, StartPipelineRunRequest
from services.orchestrator_runtime.engine import OrchestratorEngine
from services.orchestrator_runtime.persistence import db_get_run_logs
from services.orchestrator_runtime.track_profiles import resolve_track

router = APIRouter()
logger = logging.getLogger("runs")
_RUN_THREADS: dict[str, threading.Thread] = {}
_RUN_THREADS_LOCK = threading.Lock()


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


def _coerce_json_obj(val: Any) -> dict:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _resolve_run_dir(rel_or_abs_path: str | None) -> Path | None:
    if not rel_or_abs_path:
        return None
    from core.config import settings

    raw = Path(rel_or_abs_path)
    candidate = raw if raw.is_absolute() else settings.repo_root / raw
    try:
        resolved = candidate.resolve()
        resolved.relative_to(settings.repo_root.resolve())
    except Exception:
        logger.warning("Skipping unsafe run_dir_path during clear: %s", rel_or_abs_path)
        return None
    return resolved


def _select_run_columns() -> str:
    return (
        "id, slug, status, "
        "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
        "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
        "summary, pipeline_log, agent_activity, source_file_ids, "
        "track, config_json, final_status_class, replay_payload, run_dir_path"
    )


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
        track=row.track,
        config_json=_coerce_json_obj(row.config_json),
        final_status_class=row.final_status_class,
        replay_payload=_coerce_json_obj(row.replay_payload) if row.replay_payload is not None else None,
        run_dir_path=row.run_dir_path,
    )


def _validate_file_ids(
    db,
    company_id: int,
    file_ids: list[int],
    track: str | None = None,
) -> None:
    if not file_ids:
        return
    uniq = sorted(set(int(x) for x in file_ids))
    if any(i <= 0 for i in uniq):
        raise HTTPException(status_code=400, detail="Invalid file id")
    in_clause = ",".join(str(i) for i in uniq)
    if track:
        n = db.execute(
            text(
                f"SELECT COUNT(*) AS n FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause}) "
                "AND (analysis_track IS NULL OR analysis_track = :track)"
            ),
            {"cid": company_id, "track": track},
        ).scalar()
    else:
        n = db.execute(
            text(
                f"SELECT COUNT(*) AS n FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause})",
            ),
            {"cid": company_id},
        ).scalar()
    if int(n or 0) != len(uniq):
        raise HTTPException(
            status_code=400,
            detail="One or more file IDs are invalid or not allowed for this track",
        )


def _fetch_source_file_meta(db, company_id: int, file_ids: list[int]) -> list[dict[str, Any]]:
    if not file_ids:
        return []
    in_clause = ",".join(str(i) for i in sorted(set(file_ids)))
    rows = db.execute(
        text(
            f"SELECT id, original_filename, storage_relative_path, byte_size, content_type, "
            f"to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS created_at "
            f"FROM uploaded_files WHERE company_id=:cid AND id IN ({in_clause}) ORDER BY id ASC"
        ),
        {"cid": company_id},
    ).fetchall()
    return [
        {
            "id": r.id,
            "original_filename": r.original_filename,
            "storage_relative_path": r.storage_relative_path,
            "byte_size": r.byte_size,
            "content_type": r.content_type,
            "created_at": r.created_at,
        }
        for r in rows
    ]


def _run_orchestrator_in_background(
    run_id: int,
    run_slug: str,
    company_id: int,
    company_name: str,
    user_id: int,
    user_name: str,
    source_file_ids: list[int],
    source_files_meta: list[dict[str, Any]],
    onboarding_path: str | None,
    public_scrape_enabled: bool,
    skip_input_dedup: bool = False,
) -> None:
    try:
        engine = OrchestratorEngine(
            run_id=run_id,
            run_slug=run_slug,
            company_id=company_id,
            company_name=company_name,
            user_id=user_id,
            user_name=user_name,
            source_file_ids=source_file_ids,
            source_files_meta=source_files_meta,
            onboarding_path=onboarding_path,
            public_scrape_enabled=public_scrape_enabled,
            skip_input_dedup=skip_input_dedup,
        )
        engine.execute()
    except Exception:
        logger.exception("Background orchestrator failed for run %s", run_slug)
    finally:
        with _RUN_THREADS_LOCK:
            _RUN_THREADS.pop(run_slug, None)


@router.post("/start", response_model=PipelineRunOut)
def start_run(request: Request, body: StartPipelineRunRequest):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    user_id = int(user["id"])
    user_name = str(user.get("name") or "user")
    onboarding_path = body.onboarding_path or user.get("onboarding_path")
    scrape = bool(user.get("public_scrape_enabled"))

    file_ids = [int(x) for x in body.uploaded_file_ids]

    if not file_ids and not scrape:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one file or enable “Transcrape public data” in Company settings to start without uploads.",
        )

    db = SessionLocal()
    try:
        track = resolve_track(onboarding_path).value
        _validate_file_ids(db, company_id, file_ids, track=track if file_ids else None)
        source_files_meta = _fetch_source_file_meta(db, company_id, file_ids)

        slug = secrets.token_urlsafe(12).replace("-", "_")[:32]
        now = datetime.now(UTC)
        summary = (
            f"Run queued. Track: {track}. Files: {len(file_ids)}. "
            f"Public scrape mode: {scrape}."
        )

        row = db.execute(
            text(
                "INSERT INTO pipeline_runs (slug, company_id, user_id, status, started_at, "
                "summary, pipeline_log, agent_activity, source_file_ids, track, config_json) "
                "VALUES (:slug, :cid, :uid, 'pending', :st, :summary, "
                "CAST(:log AS jsonb), CAST(:agents AS jsonb), :fids, :track, CAST(:cfg AS jsonb)) "
                f"RETURNING {_select_run_columns()}"
            ),
            {
                "slug": slug,
                "cid": company_id,
                "uid": user_id,
                "st": now,
                "summary": summary,
                "log": json.dumps([f"[{slug}] Run accepted and queued for execution."]),
                "agents": json.dumps([]),
                "fids": file_ids,
                "track": track,
                "cfg": json.dumps(
                    {
                        "track": track,
                        "onboarding_path": onboarding_path,
                        "public_scrape_enabled": scrape,
                        "source_file_count": len(file_ids),
                        "force_new": bool(body.force_new),
                    },
                ),
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

    thread = threading.Thread(
        target=_run_orchestrator_in_background,
        args=(
            int(row.id),
            row.slug,
            company_id,
            user.get("company_name") or "company",
            user_id,
            user_name,
            file_ids,
            source_files_meta,
            onboarding_path,
            scrape,
            bool(body.force_new),
        ),
        name=f"run-{row.slug[:8]}",
        daemon=True,
    )
    with _RUN_THREADS_LOCK:
        _RUN_THREADS[row.slug] = thread
    thread.start()

    return _row_to_out(row)


@router.get("", response_model=list[PipelineRunOut])
def list_runs(request: Request):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                f"SELECT {_select_run_columns()} "
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
                f"SELECT {_select_run_columns()} "
                "FROM pipeline_runs WHERE company_id=:cid ORDER BY started_at DESC LIMIT 1"
            ),
            {"cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        return None
    return _row_to_out(row)


@router.get("/{slug}/logs", response_model=list[PipelineRunLogOut])
def get_run_logs(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id FROM pipeline_runs WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_get_run_logs(int(row.id))


@router.get("/{slug}/replay")
def get_run_replay(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                f"SELECT {_select_run_columns()} FROM pipeline_runs "
                "WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run = _row_to_out(row)
    logs = db_get_run_logs(int(row.id))
    return {"run": run.model_dump(), "logs": logs, "replay_payload": run.replay_payload or {}}


@router.get("/{slug}", response_model=PipelineRunOut)
def get_run(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                f"SELECT {_select_run_columns()} "
                "FROM pipeline_runs WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_out(row)


@router.delete("")
def clear_runs(request: Request):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    run_dirs: list[Path] = []
    deleted_count = 0
    try:
        active_count = int(
            db.execute(
                text(
                    "SELECT COUNT(*) FROM pipeline_runs "
                    "WHERE company_id=:cid AND status IN ('pending', 'running')"
                ),
                {"cid": company_id},
            ).scalar()
            or 0
        )
        if active_count > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cannot clear analyses while runs are active. "
                    "Wait for current runs to finish, then clear history."
                ),
            )

        rows = db.execute(
            text("SELECT id, run_dir_path FROM pipeline_runs WHERE company_id=:cid"),
            {"cid": company_id},
        ).fetchall()
        deleted_count = len(rows)
        run_dirs = [p for p in (_resolve_run_dir(r.run_dir_path) for r in rows) if p is not None]
        db.execute(
            text("DELETE FROM pipeline_runs WHERE company_id=:cid"),
            {"cid": company_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    fs_deleted = 0
    fs_errors: list[str] = []
    for run_dir in run_dirs:
        if not run_dir.exists():
            continue
        try:
            shutil.rmtree(run_dir)
            fs_deleted += 1
        except Exception as exc:
            fs_errors.append(f"{run_dir.as_posix()}: {str(exc)[:240]}")

    return {
        "status": "ok",
        "deleted_runs": deleted_count,
        "deleted_run_dirs": fs_deleted,
        "filesystem_errors": fs_errors,
    }
