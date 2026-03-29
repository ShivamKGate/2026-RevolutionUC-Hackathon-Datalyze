from __future__ import annotations

import json
import logging
import multiprocessing
import secrets
import shutil
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from db.session import SessionLocal
from schemas.files_runs import (
    PipelineRunLogOut,
    PipelineRunOut,
    RunTitlePatchRequest,
    StartPipelineRunRequest,
)
from services.run_title import propose_analysis_title_from_replay_payload
from services.orchestrator_runtime.cancellation import request_cancel_run
from services.orchestrator_runtime.persistence import db_get_run_logs
from services.orchestrator_runtime.run_job import run_orchestrator_job
from services.orchestrator_runtime.track_profiles import resolve_track

router = APIRouter()
logger = logging.getLogger("runs")

# Spawn (not fork) so the worker is a clean interpreter — safe with DB drivers; can be terminate()d.
_MP_CTX = multiprocessing.get_context("spawn")
_RUN_PROCESSES: dict[str, multiprocessing.Process] = {}
_RUN_PROCESSES_LOCK = threading.Lock()


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


def _sql_select_run_list(prefix: str = "pr") -> str:
    """Columns for list / insert return (no memory_json — keep payloads small)."""
    p = prefix
    return (
        f"{p}.id, {p}.slug, {p}.status, "
        f"to_char({p}.started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
        f"to_char({p}.ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
        f"{p}.summary, {p}.pipeline_log, {p}.agent_activity, {p}.source_file_ids, "
        f"{p}.track, {p}.config_json, {p}.final_status_class, {p}.analysis_title, "
        f"{p}.replay_payload, {p}.run_dir_path"
    )


def _sql_select_run_detail() -> str:
    return f"{_sql_select_run_list('pr')}, pr.memory_json"


def _sql_insert_returning_cols() -> str:
    """Plain column names for INSERT ... RETURNING (no table prefix)."""
    return (
        "id, slug, status, "
        "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
        "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
        "summary, pipeline_log, agent_activity, source_file_ids, "
        "track, config_json, final_status_class, analysis_title, replay_payload, run_dir_path"
    )


def _normalize_analysis_title(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _row_to_out(row, *, started_by_name: str | None = None) -> PipelineRunOut:
    sfi = row.source_file_ids
    if sfi is None:
        ids: list[int] = []
    elif isinstance(sfi, list):
        ids = [int(x) for x in sfi]
    else:
        ids = []
    mem = getattr(row, "memory_json", None)
    sbn = getattr(row, "started_by_name", None)
    if started_by_name is not None:
        sbn = started_by_name
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
        analysis_title=_normalize_analysis_title(getattr(row, "analysis_title", None)),
        memory_json=_coerce_json_obj(mem) if mem is not None else None,
        started_by_name=str(sbn).strip() if sbn else None,
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


def _reap_run_process(slug: str, proc: multiprocessing.Process) -> None:
    """Join finished worker and drop registry entry (normal completion)."""
    proc.join()
    with _RUN_PROCESSES_LOCK:
        _RUN_PROCESSES.pop(slug, None)


def _terminate_run_process(slug: str) -> None:
    """Hard-stop a worker: terminate() then kill() if needed (stops in-flight LLM calls)."""
    with _RUN_PROCESSES_LOCK:
        proc = _RUN_PROCESSES.pop(slug, None)
    if proc is None:
        return
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=4)
    if proc.is_alive():
        logger.warning("Run %s: worker still alive after terminate; sending kill", slug)
        proc.kill()
        proc.join(timeout=3)
    if proc.is_alive():
        logger.error("Run %s: worker process could not be stopped", slug)


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
                f"RETURNING {_sql_insert_returning_cols()}"
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

    proc = _MP_CTX.Process(
        target=run_orchestrator_job,
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
            bool(body.force_new),  # skip_input_dedup: "force new" bypasses 24h duplicate short-circuit
        ),
        name=f"run-{row.slug[:12]}",
        daemon=True,
    )
    with _RUN_PROCESSES_LOCK:
        _RUN_PROCESSES[row.slug] = proc
    proc.start()
    threading.Thread(
        target=_reap_run_process,
        args=(row.slug, proc),
        name=f"reap-{row.slug[:8]}",
        daemon=True,
    ).start()

    return _row_to_out(
        row,
        started_by_name=str(user.get("name") or user.get("email") or "").strip()
        or None,
    )


@router.post("/stop-active")
def stop_active_runs(request: Request):
    """
    Force-stop all pending/running analyses: terminate worker subprocesses immediately
    (in-flight LLM calls are interrupted), then mark rows cancelled in the database.
    """
    user = get_current_user(request)
    company_id, _ = _require_company(user)

    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT slug FROM pipeline_runs "
                "WHERE company_id=:cid AND status IN ('pending', 'running')"
            ),
            {"cid": company_id},
        ).fetchall()
        slugs = [str(r.slug) for r in rows]
        for slug in slugs:
            _terminate_run_process(slug)
            request_cancel_run(slug)

        db.execute(
            text(
                "UPDATE pipeline_runs SET status='cancelled', ended_at=NOW(), "
                "summary='Analysis stopped by user.' "
                "WHERE company_id=:cid AND status IN ('pending', 'running')"
            ),
            {"cid": company_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {
        "status": "ok",
        "stopped_count": len(slugs),
        "slugs": slugs,
    }


@router.get("", response_model=list[PipelineRunOut])
def list_runs(request: Request):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                f"SELECT {_sql_select_run_list()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.company_id=:cid ORDER BY pr.started_at DESC LIMIT 10000"
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
                f"SELECT {_sql_select_run_list()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.company_id=:cid ORDER BY pr.started_at DESC LIMIT 1"
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
                f"SELECT {_sql_select_run_list()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.slug=:slug AND pr.company_id=:cid"
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


def _authorized_run_dir(slug: str, company_id: int) -> Path | None:
    """Resolve on-disk run directory for this company’s run, or None if missing."""
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT run_dir_path FROM pipeline_runs "
                "WHERE slug=:slug AND company_id=:cid",
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        return None
    return _resolve_run_dir(row.run_dir_path)


@router.get("/{slug}/narration/manifest")
def get_narration_manifest(request: Request, slug: str) -> dict[str, Any]:
    """JSON index of realtime narration clips + whether final executive-summary MP3 exists."""
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    rd = _authorized_run_dir(slug, company_id)
    if rd is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not rd.is_dir():
        return {"clips": [], "final_narration": False}

    idx = rd / "artifacts" / "narration_realtime" / "index.json"
    clips: list[dict[str, Any]] = []
    if idx.is_file():
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
            raw = data.get("clips")
            if isinstance(raw, list):
                clips = [c for c in raw if isinstance(c, dict)]
        except (json.JSONDecodeError, OSError):
            clips = []

    final_narration = (rd / "artifacts" / "narration.mp3").is_file()
    return {"clips": clips, "final_narration": final_narration}


@router.get("/{slug}/narration/realtime/{seq}")
def get_narration_realtime_audio(request: Request, slug: str, seq: int) -> FileResponse:
    """Serve one realtime narration clip (matches engine: narration_realtime/{seq:04d}.mp3)."""
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    rd = _authorized_run_dir(slug, company_id)
    if rd is None or not rd.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    path = rd / "artifacts" / "narration_realtime" / f"{seq:04d}.mp3"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(path, media_type="audio/mpeg", filename=f"{seq:04d}.mp3")


@router.get("/{slug}/narration/final")
def get_narration_final_audio(request: Request, slug: str) -> FileResponse:
    """Serve executive-summary narration MP3 (artifacts/narration.mp3)."""
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    rd = _authorized_run_dir(slug, company_id)
    if rd is None or not rd.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    path = rd / "artifacts" / "narration.mp3"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Narration not ready")
    return FileResponse(path, media_type="audio/mpeg", filename="narration.mp3")


@router.patch("/{slug}/title", response_model=PipelineRunOut)
def patch_run_title(request: Request, slug: str, body: RunTitlePatchRequest):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    payload = body.model_dump(exclude_unset=True)
    if "analysis_title" not in payload:
        raise HTTPException(
            status_code=400,
            detail="Request body must include analysis_title (string or null).",
        )
    raw = payload.get("analysis_title")
    if raw is None:
        title_db = None
    else:
        t = str(raw).strip()
        title_db = t if t else None
    db = SessionLocal()
    try:
        upd = db.execute(
            text(
                "UPDATE pipeline_runs SET analysis_title=:at "
                "WHERE slug=:slug AND company_id=:cid RETURNING id"
            ),
            {"at": title_db, "slug": slug, "cid": company_id},
        ).fetchone()
        if upd is None:
            raise HTTPException(status_code=404, detail="Run not found")
        rid = int(upd.id)
        row = db.execute(
            text(
                f"SELECT {_sql_select_run_detail()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.id=:rid"
            ),
            {"rid": rid},
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
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_out(row)


@router.post("/{slug}/generate-title", response_model=PipelineRunOut)
def generate_run_title(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                f"SELECT {_sql_select_run_list()}, pr.replay_payload, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.slug=:slug AND pr.company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    st = str(row.status)
    if st not in ("completed", "completed_with_warnings"):
        raise HTTPException(
            status_code=400,
            detail="Title generation is only available for completed analyses.",
        )
    rp = _coerce_json_obj(getattr(row, "replay_payload", None))
    if not rp:
        raise HTTPException(
            status_code=400,
            detail="Run has no replay payload yet; try again shortly.",
        )
    try:
        title = propose_analysis_title_from_replay_payload(rp)
    except Exception as e:
        logger.warning("generate-title failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Could not generate a title (unexpected error).",
        ) from e
    if not (title or "").strip():
        raise HTTPException(
            status_code=502,
            detail="Could not derive a title — add an executive summary or set a title manually.",
        )

    db = SessionLocal()
    try:
        upd = db.execute(
            text(
                "UPDATE pipeline_runs SET analysis_title=:at "
                "WHERE slug=:slug AND company_id=:cid RETURNING id"
            ),
            {"at": title[:500], "slug": slug, "cid": company_id},
        ).fetchone()
        if upd is None:
            raise HTTPException(status_code=404, detail="Run not found")
        rid = int(upd.id)
        row2 = db.execute(
            text(
                f"SELECT {_sql_select_run_detail()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.id=:rid"
            ),
            {"rid": rid},
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
    if row2 is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_out(row2)


@router.get("/{slug}", response_model=PipelineRunOut)
def get_run(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                f"SELECT {_sql_select_run_detail()}, "
                "COALESCE(u.name, u.email, 'Teammate') AS started_by_name "
                "FROM pipeline_runs pr "
                "LEFT JOIN users u ON u.id = pr.user_id "
                "WHERE pr.slug=:slug AND pr.company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_out(row)


@router.post("/{slug}/stop")
def stop_single_run(request: Request, slug: str):
    """Force-stop one pending/running analysis (same semantics as stop-active, scoped to slug)."""
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id, status FROM pipeline_runs "
                "WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(row.status) not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail="Run is not active (only pending or running can be stopped).",
        )

    _terminate_run_process(slug)
    request_cancel_run(slug)

    db = SessionLocal()
    try:
        db.execute(
            text(
                "UPDATE pipeline_runs SET status='cancelled', ended_at=NOW(), "
                "summary='Analysis stopped by user.' "
                "WHERE company_id=:cid AND slug=:slug AND status IN ('pending', 'running')"
            ),
            {"cid": company_id, "slug": slug},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"status": "ok", "slug": slug}


@router.delete("/{slug}")
def delete_single_run(request: Request, slug: str):
    """Remove one finished run from history and delete its artifact directory."""
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    row = None
    try:
        row = db.execute(
            text(
                "SELECT id, status, run_dir_path FROM pipeline_runs "
                "WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(row.status) in ("pending", "running"):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an active run. Stop it first.",
        )

    run_dir = _resolve_run_dir(row.run_dir_path)
    db = SessionLocal()
    try:
        db.execute(
            text("DELETE FROM pipeline_runs WHERE id=:id AND company_id=:cid"),
            {"id": int(row.id), "cid": company_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    fs_errors: list[str] = []
    if run_dir is not None and run_dir.exists():
        try:
            shutil.rmtree(run_dir)
        except Exception as exc:
            fs_errors.append(f"{run_dir.as_posix()}: {str(exc)[:240]}")

    return {
        "status": "ok",
        "slug": slug,
        "filesystem_errors": fs_errors,
    }


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
