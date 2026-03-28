"""
Application settings are loaded from `apps/api/.env` (see `.env.example`).

Pydantic Settings maps env vars to fields (e.g. HEAVY_MODEL → heavy_model). Do not
duplicate business defaults here: set values in `.env`. Only optional secrets use an
empty-string default when the variable is absent.
"""

from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
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
    orchestrator_max_retries: int = Field(default=2)
    orchestrator_timeout_seconds: int = Field(default=45)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash")
    elevenlabs_api_key: str = Field(default="")

    @field_validator("orchestrator_max_retries", "orchestrator_timeout_seconds", mode="before")
    @classmethod
    def _empty_int_uses_default(cls, v: object, info: ValidationInfo) -> object:
        if isinstance(v, str) and not v.strip():
            if info.field_name == "orchestrator_max_retries":
                return 2
            return 45
        return v

    @field_validator(
        "llm_provider",
        "llm_base_url",
        "heavy_model",
        "heavy_alt_model",
        "light_model",
        "embedding_model",
        "gemini_model",
        mode="before",
    )
    @classmethod
    def _strip_modelish_strings(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @property
    def gemini_api_key_configured(self) -> bool:
        return bool((self.gemini_api_key or "").strip())

    @property
    def elevenlabs_api_key_configured(self) -> bool:
        return bool((self.elevenlabs_api_key or "").strip())

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
