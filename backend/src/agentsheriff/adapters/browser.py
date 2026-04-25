from __future__ import annotations

from typing import Any

from ._common import ok, require_gateway_token, text_arg
from ._seed import fresh_state


def open(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    url = text_arg(args, "url", "https://example.com/team-checkin")
    pages = fresh_state()["browser"]["pages"]
    return ok("browser.open", url=url, title=_title_for(url), loaded=url in pages)


def extract_text(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    url = text_arg(args, "url", "https://example.com/team-checkin")
    text = fresh_state()["browser"]["pages"].get(url, "")
    return ok("browser.extract_text", url=url, text=text, chars=len(text))


def _title_for(url: str) -> str:
    if "evil.test" in url:
        return "Suspicious Demo Page"
    return "AgentSheriff Demo Page"
