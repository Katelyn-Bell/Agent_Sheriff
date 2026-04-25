from __future__ import annotations

from typing import Any

from ._common import list_arg, ok, require_gateway_token, stable_id, text_arg
from ._seed import fresh_state


def list_events(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    state = fresh_state()
    date = text_arg(args, "date")
    events = state["calendar"]["events"]
    if date:
        events = [event for event in events if event["start"].startswith(date)]
    return ok("calendar.list_events", events=events, count=len(events))


def create_event(*, args: dict[str, Any], gateway_token: str) -> dict[str, Any]:
    require_gateway_token(gateway_token)
    title = text_arg(args, "title", "Untitled event")
    attendees = list_arg(args, "attendees")
    start = text_arg(args, "start", "2026-04-25T15:00:00-04:00")
    duration_minutes = int(args.get("duration_minutes", 30))
    event_id = stable_id("evt", title, tuple(attendees), start, duration_minutes)
    return ok(
        "calendar.create_event",
        event={
            "id": event_id,
            "title": title,
            "attendees": attendees,
            "start": start,
            "duration_minutes": duration_minutes,
        },
    )
