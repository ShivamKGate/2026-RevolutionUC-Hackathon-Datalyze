from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Datalyze API"
    environment: str = "development"
    allowed_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    ollama_host: str = "http://127.0.0.1:11434"
    heavy_model: str = "qwen2.5:14b"
    light_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


settings = Settings()
