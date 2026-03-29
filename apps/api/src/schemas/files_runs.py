from pydantic import BaseModel, Field


class UploadedFileOut(BaseModel):
    id: int
    original_filename: str
    byte_size: int
    visibility: str
    content_type: str | None
    created_at: str


class StartPipelineRunRequest(BaseModel):
    uploaded_file_ids: list[int] = Field(default_factory=list)


class PipelineRunOut(BaseModel):
    id: int
    slug: str
    status: str
    started_at: str
    ended_at: str | None
    summary: str | None
    pipeline_log: list
    agent_activity: list
    source_file_ids: list[int]
    track: str | None = None
    config_json: dict = Field(default_factory=dict)
    final_status_class: str | None = None
    replay_payload: dict | None = None
    run_dir_path: str | None = None


class PipelineRunLogOut(BaseModel):
    id: int
    timestamp: str | None = None
    stage: str
    agent: str
    action: str
    detail: str
    status: str
    meta: dict = Field(default_factory=dict)
