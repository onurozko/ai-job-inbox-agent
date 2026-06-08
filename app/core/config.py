from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    secret_key: str = Field(default="change-me-in-production")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7)
    oauth_state_expire_minutes: int = Field(default=10)
    auth_frontend_redirect_url: str = "http://localhost:3000/auth/callback"

    database_url: str = Field(
        default="postgresql+asyncpg://jobinbox:jobinbox@localhost:5432/jobinbox"
    )

    openai_api_key: str | None = None

    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    gmail_connect_redirect_uri: str = "http://localhost:8000/api/v1/auth/gmail/callback"

    cors_origins: str = "*"

    enable_background_sync: bool = Field(default=False)
    background_sync_interval_minutes: int = Field(default=30, ge=1)
    background_sync_max_results: int = Field(default=25, ge=1)

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
