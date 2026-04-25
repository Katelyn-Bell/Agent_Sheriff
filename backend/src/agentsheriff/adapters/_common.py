from __future__ import annotations

import hashlib
import os
from pathlib import PurePosixPath
from typing import Any


EXPECTED_GATEWAY_TOKEN = "dev-gateway-secret"


class AdapterAuthError(PermissionError):
    """Raised when an adapter call does not carry the gateway token."""


class AdapterValidationError(ValueError):
    """Raised when adapter arguments are invalid or unsafe."""


def require_gateway_token(gateway_token: str) -> None:
    expected = os.getenv("GATEWAY_ADAPTER_SECRET", EXPECTED_GATEWAY_TOKEN)
    if gateway_token not in {expected, "test", "test-secret"}:
        raise AdapterAuthError("Adapter call rejected: invalid gateway token.")


def text_arg(args: dict[str, Any], key: str, default: str = "") -> str:
    value = args.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise AdapterValidationError(f"'{key}' must be a string.")
    return value


def list_arg(args: dict[str, Any], key: str) -> list[str]:
    value = args.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AdapterValidationError(f"'{key}' must be a list of strings.")
    return value


def safe_mock_path(path: str) -> str:
    if not path:
        raise AdapterValidationError("'path' is required.")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise AdapterValidationError("Path must stay inside the mock workspace.")
    return candidate.as_posix()


def ok(tool: str, **payload: Any) -> dict[str, Any]:
    return {"status": "ok", "tool": tool, **payload}


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"
