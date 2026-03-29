from __future__ import annotations

from fastapi import APIRouter, Request

from api.v1.routes.auth import get_current_user
from api.v1.routes.runs import _require_company, execute_pipeline_start
from schemas.files_runs import DatalyzeChatRequest, DatalyzeChatResponse
from services.datalyze_chat import datalyze_turn

router = APIRouter()


@router.post("/datalyze", response_model=DatalyzeChatResponse)
def post_datalyze_chat(request: Request, body: DatalyzeChatRequest):
    user = get_current_user(request)
    return datalyze_turn(
        user=user,
        body=body,
        execute_pipeline_start=execute_pipeline_start,
        require_company=_require_company,
    )
