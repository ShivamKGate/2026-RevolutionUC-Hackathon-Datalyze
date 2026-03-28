"""
Application settings are loaded from `apps/api/.env` (see `.env.example`).

Pydantic Settings maps env vars to fields (e.g. HEAVY_MODEL → heavy_model). Do not
duplicate business defaults here: set values in `.env`. Only optional secrets use an
empty-string default when the variable is absent.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str
    environment: str
    allowed_origins_raw: str
    llm_provider: str
    llm_base_url: str
    llm_api_key: str = Field(default="")
    heavy_model: str
    heavy_alt_model: str
    light_model: str
    embedding_model: str
    database_url: str = Field(default="")
    orchestrator_max_retries: int
    orchestrator_timeout_seconds: int
    gemini_api_key: str = Field(default="")
    elevenlabs_api_key: str = Field(default="")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]

    @property
    def llm_api_key_configured(self) -> bool:
        k = (self.llm_api_key or "").strip()
        if not k or k == "DATALYZE_PLACEHOLDER_KEY":
            return False
        return True


settings = Settings()
