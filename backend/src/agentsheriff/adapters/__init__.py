from __future__ import annotations

from . import browser, calendar, files, github, gmail, shell
from .manifest import ALL_TOOLS, DISPATCH, get_tool, manifest_for_json, namespace_map, supported_tools, tools_by_namespace


DISPATCH.update({
    "gmail.read_inbox": gmail.read_inbox,
    "gmail.send_email": gmail.send_email,
    "calendar.list_events": calendar.list_events,
    "calendar.create_event": calendar.create_event,
    "files.read": files.read,
    "files.write": files.write,
    "github.create_issue": github.create_issue,
    "github.push_branch": github.push_branch,
    "browser.open": browser.open,
    "browser.extract_text": browser.extract_text,
    "shell.run": shell.run,
})


__all__ = [
    "ALL_TOOLS",
    "DISPATCH",
    "get_tool",
    "manifest_for_json",
    "namespace_map",
    "supported_tools",
    "tools_by_namespace",
]
