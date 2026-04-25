from __future__ import annotations

from typing import Any, Callable


def _stub_dispatch(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    _ = gateway_token
    return {"status": "stubbed", "args": args}


DISPATCH: dict[str, Callable[..., dict[str, Any]]] = {
    "gmail.read_inbox": _stub_dispatch,
    "gmail.send_email": _stub_dispatch,
    "calendar.create_event": _stub_dispatch,
    "files.read": _stub_dispatch,
    "github.push_branch": _stub_dispatch,
    "shell.run": _stub_dispatch,
    "browser.open": _stub_dispatch,
}


def supported_tools() -> set[str]:
    return set(DISPATCH)
