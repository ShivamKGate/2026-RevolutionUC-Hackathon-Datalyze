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


class AgentMVPResponse(BaseModel):
    status: str
    run_executed: bool
    ollama_host: str
    heavy_model: str
    light_model: str
    embedding_model: str
    agents_initialized: list[str]
    tasks_initialized: int
    output: str | None = None
