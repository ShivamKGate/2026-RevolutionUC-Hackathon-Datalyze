from pydantic import BaseModel


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
    initialized_agents: int
    local_agents: int
    external_agents: int
    system_agents: int
    errors: list[str]
    agents: list[BootAgentNodeResponse]
    orchestrator_policy: dict[str, int]
