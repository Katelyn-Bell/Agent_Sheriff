from __future__ import annotations

from typing import Any

from ._common import ok, require_gateway_token, safe_mock_path, text_arg
from ._seed import fresh_state


def read(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    path = safe_mock_path(text_arg(args, "path"))
    files = fresh_state()["files"]
    if path not in files:
        return ok("files.read", path=path, found=False, content="")
    return ok("files.read", path=path, found=True, content=files[path])


def write(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    path = safe_mock_path(text_arg(args, "path"))
    content = text_arg(args, "content")
    return ok("files.write", path=path, bytes_written=len(content.encode("utf-8")), persisted="mock-only")
