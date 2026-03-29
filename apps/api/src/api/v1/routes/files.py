from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from sqlalchemy import text

from api.v1.routes.auth import get_current_user
from core.config import settings
from db.session import SessionLocal
from schemas.files_runs import UploadedFileOut
from services.company_paths import company_data_private_dir, relative_posix_path

router = APIRouter()

_ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".pdf", ".txt", ".md"}

_DEMO_EMAIL = "demo@revuc.com"
_DEMO_COMPANY = "E2E_Analytics_Co"


def _mirror_upload_for_demo_company(
    dest_path: Path,
    company_name: str,
    user_email: str,
    analysis_track: str | None,
    safe_base: str,
) -> None:
    if user_email.strip().lower() != _DEMO_EMAIL or company_name.strip() != _DEMO_COMPANY:
        return
    sub = (analysis_track or "general").strip().lower().replace(" ", "_")
    if sub not in (
        "predictive",
        "automation",
        "optimization",
        "supply_chain",
        "general",
    ):
        sub = "general"
    e2e_dir = (
        settings.repo_root
        / "Miscellaneous"
        / "data"
        / "sources"
        / "E2E_Analytics_Co"
        / sub
    )
    e2e_dir.mkdir(parents=True, exist_ok=True)
    target = e2e_dir / safe_base
    try:
        shutil.copy2(dest_path, target)
    except OSError:
        pass


def _require_company(user: dict) -> tuple[int, str]:
    cid = user.get("company_id")
    cname = user.get("company_name") or ""
    if cid is None:
        raise HTTPException(status_code=400, detail="User has no company assigned")
    if not cname.strip():
        cname = "company"
    return int(cid), cname.strip()


def _safe_delete_stored_file(relative_path: str) -> None:
    abs_path = (settings.repo_root / Path(relative_path)).resolve()
    data_root = (settings.repo_root / "data").resolve()
    if not str(abs_path).startswith(str(data_root)):
        return
    if abs_path.is_file():
        abs_path.unlink(missing_ok=True)


@router.post("/upload", response_model=UploadedFileOut)
def upload_file(
    request: Request,
    file: UploadFile,
    analysis_track: str | None = Form(None),
):
    user = get_current_user(request)
    company_id, company_name = _require_company(user)
    user_id = int(user["id"])
    user_email = str(user.get("email") or "")

    raw_name = file.filename or "upload"
    suffix = Path(raw_name).suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(_ALLOWED_SUFFIXES))}",
        )

    safe_base = Path(raw_name).name[:180] if Path(raw_name).name else "file"
    stored_filename = f"{uuid4().hex}_{safe_base}"
    dest_dir = company_data_private_dir(company_name)
    dest_path = dest_dir / stored_filename

    try:
        with dest_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    finally:
        file.file.close()

    byte_size = dest_path.stat().st_size
    rel = relative_posix_path(dest_path)
    content_type = file.content_type
    track_val = (analysis_track or "").strip() or None

    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "INSERT INTO uploaded_files (company_id, user_id, original_filename, stored_filename, "
                "storage_relative_path, visibility, byte_size, content_type, analysis_track) "
                "VALUES (:cid, :uid, :orig, :stored, :path, 'private', :size, :ct, :at) "
                "RETURNING id, original_filename, byte_size, visibility, content_type, analysis_track, "
                "to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS created_at"
            ),
            {
                "cid": company_id,
                "uid": user_id,
                "orig": safe_base,
                "stored": stored_filename,
                "path": rel,
                "size": byte_size,
                "ct": content_type,
                "at": track_val,
            },
        ).fetchone()
        db.commit()
    except Exception:
        db.rollback()
        dest_path.unlink(missing_ok=True)
        raise
    finally:
        db.close()

    _mirror_upload_for_demo_company(
        dest_path, company_name, user_email, track_val, safe_base,
    )

    return UploadedFileOut(
        id=row.id,
        original_filename=row.original_filename,
        byte_size=row.byte_size,
        visibility=row.visibility,
        content_type=row.content_type,
        created_at=row.created_at,
        analysis_track=getattr(row, "analysis_track", None),
    )


@router.get("", response_model=list[UploadedFileOut])
def list_files(request: Request, track: str | None = None):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    try:
        t = (track or "").strip()
        if t:
            rows = db.execute(
                text(
                    "SELECT id, original_filename, byte_size, visibility, content_type, analysis_track, "
                    "to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS created_at "
                    "FROM uploaded_files WHERE company_id=:cid "
                    "AND (analysis_track IS NULL OR analysis_track = :track) "
                    "ORDER BY created_at DESC"
                ),
                {"cid": company_id, "track": t},
            ).fetchall()
        else:
            rows = db.execute(
                text(
                    "SELECT id, original_filename, byte_size, visibility, content_type, analysis_track, "
                    "to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') AS created_at "
                    "FROM uploaded_files WHERE company_id=:cid ORDER BY created_at DESC"
                ),
                {"cid": company_id},
            ).fetchall()
    finally:
        db.close()
    return [
        UploadedFileOut(
            id=r.id,
            original_filename=r.original_filename,
            byte_size=r.byte_size,
            visibility=r.visibility,
            content_type=r.content_type,
            created_at=r.created_at,
            analysis_track=getattr(r, "analysis_track", None),
        )
        for r in rows
    ]


@router.delete("/{file_id}")
def delete_file(request: Request, file_id: int):
    user = get_current_user(request)
    company_id, _ = _require_company(user)
    db = SessionLocal()
    rel_path: str | None = None
    try:
        row = db.execute(
            text(
                "SELECT storage_relative_path FROM uploaded_files WHERE id=:fid AND company_id=:cid"
            ),
            {"fid": file_id, "cid": company_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="File not found")
        rel_path = row.storage_relative_path
        db.execute(
            text("DELETE FROM uploaded_files WHERE id=:fid AND company_id=:cid"),
            {"fid": file_id, "cid": company_id},
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if rel_path:
        _safe_delete_stored_file(rel_path)

    return {"ok": True, "id": file_id}
