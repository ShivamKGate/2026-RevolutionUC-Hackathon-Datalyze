from pydantic import BaseModel, Field


class AgentMVPRequest(BaseModel):
    company_context: str = Field(
        default="Small business with mixed sales and operations files.",
        min_length=3,
    )
    user_goal: str = Field(
        default="Find key business risks and top growth opportunities.",
        min_length=3,
    )
    run: bool = False


class GeminiAgentVerifyRequest(BaseModel):
    message: str = Field(
        default="Reply with one short friendly sentence confirming you are working.",
        min_length=1,
        max_length=4000,
    )


class GeminiAgentVerifyResponse(BaseModel):
    agent_id: str
    agent_name: str
    model: str
    reply: str


class ElevenLabsAgentVerifyRequest(BaseModel):
    text: str = Field(
        default="This is a quick test of executive summary narration.",
        min_length=1,
        max_length=2500,
    )


class ElevenLabsAgentVerifyResponse(BaseModel):
    agent_id: str
    agent_name: str
    mp3_bytes: int
    detail: str


class AgentHealthCheckItem(BaseModel):
    agent_id: str
    agent_name: str
    model_type: str
    model: str
    runtime_kind: str
    status: str
    detail: str
    reply_preview: str | None = None


class AgentHealthCheckResponse(BaseModel):
    status: str
    checks_total: int
    checks_passed: int
    checks_failed: int
    checks_skipped: int
    results: list[AgentHealthCheckItem]


class AgentMVPResponse(BaseModel):
    status: str
    run_executed: bool
    llm_provider: str
    llm_base_url: str
    heavy_model: str
    heavy_alt_model: str
    light_model: str
    embedding_model: str
    agents_initialized: list[str]
    tasks_initialized: int
    output: str | None = None
