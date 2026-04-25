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
    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    approval_timeout_s: int = Field(default=120, alias="APPROVAL_TIMEOUT_S")
    gateway_adapter_secret: str = Field(default="dev-gateway-secret", alias="GATEWAY_ADAPTER_SECRET")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    use_llm_classifier: bool = Field(default=True, alias="USE_LLM_CLASSIFIER")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    policy_path: str | None = Field(default=None, alias="POLICY_PATH")

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
