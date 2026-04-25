from __future__ import annotations

import json
import logging
import sys
from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./sheriff.db", alias="DATABASE_URL")
    frontend_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="FRONTEND_ORIGINS",
    )
    approval_timeout_s: int = Field(default=120, alias="APPROVAL_TIMEOUT_S")
    gateway_adapter_secret: str = Field(default="dev-gateway-secret", alias="GATEWAY_ADAPTER_SECRET")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-5-mini", alias="OPENROUTER_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.4-mini", alias="OPENAI_MODEL")
    use_llm_classifier: bool = Field(default=True, alias="USE_LLM_CLASSIFIER")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    policy_path: str | None = Field(default=None, alias="POLICY_PATH")

    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri: str = Field(
        default="http://localhost:8000/v1/auth/google/callback",
        alias="OAUTH_REDIRECT_URI",
    )
    session_secret: str = Field(
        default="dev-session-secret-change-me", alias="SESSION_SECRET"
    )
    session_cookie_name: str = Field(
        default="agentsheriff_session", alias="SESSION_COOKIE_NAME"
    )
    session_max_age_s: int = Field(default=604800, alias="SESSION_MAX_AGE_S")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    configure_logging(settings.log_level)
    return settings
