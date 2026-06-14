from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sunday:sunday_dev_only_change_me@localhost:5432/sunday"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    anthropic_api_key: str = ""
    anthropic_region: str = "eu"
    # Optional override for EU data-residency endpoint (see docs/LEGAL.md).
    anthropic_base_url: str = ""
    # Two-tier model split (docs/ARCHITECTURE.md). Chat uses Sonnet; the cheap
    # guardrail/summarisation tier uses Haiku.
    anthropic_chat_model: str = "claude-sonnet-4-6"
    anthropic_guard_model: str = "claude-haiku-4-5"
    chat_max_tokens: int = 1024
    fmp_api_key: str = ""

    demo_user_id: int = 1

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
