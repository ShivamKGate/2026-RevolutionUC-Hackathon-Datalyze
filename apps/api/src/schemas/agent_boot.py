from pydantic import BaseModel, Field


class BootAgentNodeResponse(BaseModel):
    id: str
    name: str
    model_type: str
    model_resolved: str
    runtime_kind: str
    priority: str
    responsibilities: str
    input_description: str
    output_description: str
    dependencies: list[str]
    dependencies_resolved: bool
    unresolved_dependencies: list[str]
    implementation_notes: str
    initialized: bool


class AgentBootStatusResponse(BaseModel):
    status: str
    booted_at: str | None
    total_agents: int
    initialized_agents: int = Field(
        description="Agents with a successful registry slot (CrewAI LLM built, or non-LLM stub).",
    )
    crewai_total: int = Field(
        description="Agents backed by CrewAI + configured LLM provider.",
    )
    crewai_initialized: int = Field(
        description="CrewAI agents whose LLM instance constructed successfully (install litellm for custom Featherless model slugs).",
    )
    init_summary: str
    local_agents: int
    external_agents: int
    system_agents: int
    errors: list[str]
    agents: list[BootAgentNodeResponse]
    orchestrator_policy: dict[str, int]
