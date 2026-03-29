"""PDF export routes for pipeline runs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from db.session import SessionLocal
from services.export_html import generate_html_report
from services.export_pdf import generate_pdf_report

router = APIRouter()
logger = logging.getLogger("exports")


def _require_company(user: dict) -> tuple[int, str]:
    cid = user.get("company_id")
    cname = user.get("company_name") or ""
    if cid is None:
        raise HTTPException(status_code=400, detail="User has no company assigned")
    if not cname.strip():
        cname = "company"
    return int(cid), cname.strip()


def _coerce_json_list(val) -> list:
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


def _coerce_json_obj(val) -> dict:
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
        logger.warning("Skipping unsafe run_dir_path: %s", rel_or_abs_path)
        return None
    return resolved


@router.get("/{slug}/export/pdf")
async def export_run_pdf(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)

    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids, "
                "track, config_json, final_status_class, replay_payload, run_dir_path "
                "FROM pipeline_runs WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = _resolve_run_dir(row.run_dir_path)
    if run_dir is None or not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="Run output directory not found")

    run_data = {
        "id": row.id,
        "slug": row.slug,
        "status": row.status,
        "started_at": row.started_at,
        "ended_at": row.ended_at,
        "summary": row.summary,
        "pipeline_log": _coerce_json_list(row.pipeline_log),
        "agent_activity": _coerce_json_list(row.agent_activity),
        "track": row.track,
        "config_json": _coerce_json_obj(row.config_json),
        "final_status_class": row.final_status_class,
    }

    replay_payload = _coerce_json_obj(row.replay_payload)

    pdf_bytes = await generate_pdf_report(
        run_slug=slug,
        run_dir=str(run_dir),
        run_data=run_data,
        replay_payload=replay_payload,
    )

    filename = f"datalyze-report-{slug}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{slug}/export/html")
async def export_run_html(request: Request, slug: str):
    user = get_current_user(request)
    company_id, _ = _require_company(user)

    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT id, slug, status, "
                "to_char(started_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS started_at, "
                "to_char(ended_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS ended_at, "
                "summary, pipeline_log, agent_activity, source_file_ids, "
                "track, config_json, final_status_class, replay_payload, run_dir_path "
                "FROM pipeline_runs WHERE slug=:slug AND company_id=:cid"
            ),
            {"slug": slug, "cid": company_id},
        ).fetchone()
    finally:
        db.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = _resolve_run_dir(row.run_dir_path)
    if run_dir is None or not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="Run output directory not found")

    replay_payload = _coerce_json_obj(row.replay_payload)
    if not replay_payload:
        replay_payload = {}

    run_data = {
        "id": row.id,
        "slug": row.slug,
        "status": row.status,
        "started_at": row.started_at,
        "ended_at": row.ended_at,
        "summary": row.summary,
        "pipeline_log": _coerce_json_list(row.pipeline_log),
        "agent_activity": _coerce_json_list(row.agent_activity),
        "track": row.track,
        "config_json": _coerce_json_obj(row.config_json),
        "final_status_class": row.final_status_class,
    }

    html_str = generate_html_report(
        run_slug=slug,
        run_dir=str(run_dir),
        run_data=run_data,
        replay_payload=replay_payload,
    )

    filename = f"datalyze-report-{slug}.html"
    return Response(
        content=html_str,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
