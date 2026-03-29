from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from api.v1.routes.auth import get_current_user
from services.orchestrator_runtime.persistence import db_get_demo_replay, db_list_demo_replays

router = APIRouter()


def _require_admin(user: dict) -> None:
    if (user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/replay")
def list_replays(request: Request) -> list[dict[str, Any]]:
    user = get_current_user(request)
    _require_admin(user)
    cid = user.get("company_id")
    if cid is None:
        raise HTTPException(status_code=400, detail="User has no company")
    return db_list_demo_replays(int(cid))


@router.get("/replay/{track}")
def get_replay(request: Request, track: str) -> dict[str, Any]:
    user = get_current_user(request)
    _require_admin(user)
    cid = user.get("company_id")
    if cid is None:
        raise HTTPException(status_code=400, detail="User has no company")
    row = db_get_demo_replay(int(cid), track.strip().lower())
    if not row:
        raise HTTPException(status_code=404, detail="No replay for this track")
    return row
