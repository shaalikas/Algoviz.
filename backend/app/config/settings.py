from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    ai_engine_url: str = "http://localhost:8100"
    ai_engine_timeout_seconds: float = 35.0
    max_upload_bytes: int = 30 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
