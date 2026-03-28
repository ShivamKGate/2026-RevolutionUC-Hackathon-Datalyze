from pydantic import BaseModel, Field

from core.ollama_models import OllamaModelEntry


class OllamaCatalogResponse(BaseModel):
    hardware_summary: str
    defaults: dict[str, str] = Field(
        description="Active env-driven defaults for this API instance.",
    )
    models: list[OllamaModelEntry]
    pull_commands: list[str]
    llm_api_key_configured: bool
    llm_sanity_message: str
