"""
Application settings are loaded from `apps/api/.env` (see `.env.example`).

Pydantic Settings maps env vars to fields (e.g. HEAVY_MODEL → heavy_model). Do not
duplicate business defaults here: set values in `.env`. Only optional secrets use an
empty-string default when the variable is absent.
"""

from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator, model_validator
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
    llm_provider: str = Field(default="featherless")
    llm_base_url: str = Field(default="")
    llm_api_key: str = Field(default="")
    heavy_model: str
    heavy_alt_model: str = Field(default="")
    light_model: str
    embedding_model: str
    database_url: str = Field(default="")
    orchestrator_max_retries: int = Field(default=2)
    orchestrator_timeout_seconds: int = Field(default=45)
    # Orchestrator runtime policy flags
    orch_enable_parallel_branches: bool = Field(default=False)
    orch_enable_adaptive_policy: bool = Field(default=False)
    orch_enable_stage_gates: bool = Field(default=True)
    orch_max_run_seconds: int = Field(default=900)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash")
    elevenlabs_api_key: str = Field(default="")
    jwt_secret: str = Field(default="change-me-in-production-use-a-long-random-string")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_hours: int = Field(default=48)
    cookie_name: str = Field(default="datalyze_token")
    cookie_secure: bool = Field(default=False)

    @field_validator(
        "orchestrator_max_retries", "orchestrator_timeout_seconds", "orch_max_run_seconds",
        mode="before",
    )
    @classmethod
    def _empty_int_uses_default(cls, v: object, info: ValidationInfo) -> object:
        if isinstance(v, str) and not v.strip():
            defaults = {
                "orchestrator_max_retries": 2,
                "orchestrator_timeout_seconds": 45,
                "orch_max_run_seconds": 900,
            }
            return defaults.get(info.field_name, 0)
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

    @field_validator("jwt_expire_hours", mode="before")
    @classmethod
    def _empty_jwt_hours_uses_default(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            return 48
        return v

    @model_validator(mode="after")
    def _apply_llm_defaults(self) -> "Settings":
        """CrewAI inference uses Featherless only (OpenAI-compatible HTTP API, no local Ollama)."""
        featherless_default_base = "https://api.featherless.ai/v1"
        if not self.llm_base_url:
            self.llm_base_url = featherless_default_base
        # Legacy .env files used local Ollama (:11434); migrate base URL to Featherless.
        if ":11434" in self.llm_base_url:
            self.llm_base_url = featherless_default_base
        self.llm_provider = "featherless"
        if not self.heavy_alt_model:
            self.heavy_alt_model = self.heavy_model
        return self

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
    def repo_root(self) -> Path:
        # apps/api/src/core/config.py → parents[4] = repository root (contains apps/, data/)
        return Path(__file__).resolve().parents[4]

    @property
    def llm_api_key_configured(self) -> bool:
        k = (self.llm_api_key or "").strip()
        if not k or k == "DATALYZE_PLACEHOLDER_KEY":
            return False
        return True


settings = Settings()
