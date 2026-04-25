from __future__ import annotations

from typing import Any

from ._common import list_arg, ok, require_gateway_token, stable_id, text_arg
from ._seed import fresh_state


def read_inbox(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    state = fresh_state()
    query = text_arg(args, "query").lower()
    limit = int(args.get("limit", 10))
    messages = state["gmail"]["inbox"]
    if query:
        messages = [
            message for message in messages
            if query in message["subject"].lower() or query in message["body"].lower()
        ]
    return ok("gmail.read_inbox", messages=messages[:limit], count=len(messages[:limit]))


def send_email(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    to = text_arg(args, "to")
    subject = text_arg(args, "subject", "(no subject)")
    body = text_arg(args, "body")
    attachments = list_arg(args, "attachments")
    message_id = stable_id("sent", to, subject, body, tuple(attachments))
    return ok(
        "gmail.send_email",
        message_id=message_id,
        to=to,
        subject=subject,
        body_preview=body[:120],
        attachments=attachments,
        delivered=True,
    )
