from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Mini Agent Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://map:map@localhost:5432/map"
    redis_url: str = "redis://localhost:6379"

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    max_prompt_length: int = 10_000
    max_name_length: int = 100
    max_description_length: int = 1_000
    max_role_length: int = 100

    default_page_limit: int = 20
    max_page_limit: int = 100

    allowed_models: List[str] = [
        "gpt-5",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "claude-4-opus",
        "claude-4.5-sonnet",
        "gemini-2.5 pro",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
