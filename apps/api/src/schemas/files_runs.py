from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class AnalysisChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


class AnalysisChatResponse(BaseModel):
    reply: str


class DatalyzeChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    uploaded_file_ids: list[int] = Field(default_factory=list)
    enable_public_scrape: bool = False
    """
    predictive | automation | optimization | supply_chain, or auto to classify from
    prompt + files + public-scrape setting before the run starts.
    """
    custom_base_track: str = "auto"


class UploadedFileOut(BaseModel):
    id: int
    original_filename: str
    byte_size: int
    visibility: str
    content_type: str | None
    created_at: str
    analysis_track: str | None = None


class StartPipelineRunRequest(BaseModel):
    uploaded_file_ids: list[int] = Field(default_factory=list)
    """Optional onboarding path for this run only (e.g. Deep Analysis → predictive)."""
    onboarding_path: str | None = None
    """When true, skip 24h duplicate-input short-circuit."""
    force_new: bool = False
    """When set, overrides the user's company default for this run only (e.g. Datalyze Chat toggle)."""
    public_scrape_enabled: bool | None = None
    """
    Datalyze Chat only: canonical base id (predictive, automation, optimization, supply_chain).
    Stored in config_json; the API maps this to a normal onboarding_path for the orchestrator.
    """
    custom_base_track: str | None = None
    pipeline_selection_rationale: str | None = Field(
        default=None,
        max_length=2000,
        description="Auto-selection rationale stored in config_json.",
    )
    datalyze_user_instruction: str | None = Field(
        default=None,
        max_length=4000,
        description="Latest user goal from Datalyze Chat (config_json).",
    )
    relax_file_track_validation: bool = Field(
        default=False,
        description="Datalyze Chat: accept any company uploads regardless of analysis_track.",
    )


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
    analysis_title: str | None = Field(
        default=None,
        description="Custom dashboard title; empty means UI shows run id.",
    )
    memory_json: dict | None = Field(
        default=None,
        description="Orchestrator memory snapshot; usually only on GET one run.",
    )
    started_by_name: str | None = Field(
        default=None,
        description="Run owner for company-wide lists.",
    )


class DatalyzeChatResponse(BaseModel):
    reply: str
    started_run: PipelineRunOut | None = None


class RunTitlePatchRequest(BaseModel):
    """`analysis_title`: set a label, or `null` / empty string to clear."""

    analysis_title: str | None = Field(default=None, max_length=500)


class PipelineRunLogOut(BaseModel):
    id: int
    timestamp: str | None = None
    stage: str
    agent: str
    action: str
    detail: str
    status: str
    meta: dict = Field(default_factory=dict)
