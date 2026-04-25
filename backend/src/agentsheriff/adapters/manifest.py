from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


AdapterCallable = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    namespace: str
    label: str
    risk_hints: tuple[str, ...] = ()
    args_schema_summary: dict[str, str] = field(default_factory=dict)
    replay_safe: bool = True


ALL_TOOLS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        id="gmail.read_inbox",
        namespace="gmail",
        label="Read inbox",
        risk_hints=("reads_private_content",),
        args_schema_summary={"query": "Optional search text.", "limit": "Maximum messages to return."},
    ),
    ToolDefinition(
        id="gmail.send_email",
        namespace="gmail",
        label="Send email",
        risk_hints=("external_recipient", "sensitive_attachment", "data_exfiltration"),
        args_schema_summary={
            "to": "Recipient email address.",
            "subject": "Email subject.",
            "body": "Email body.",
            "attachments": "List of local mock attachment names.",
        },
        replay_safe=False,
    ),
    ToolDefinition(
        id="calendar.list_events",
        namespace="calendar",
        label="List calendar events",
        risk_hints=("reads_schedule",),
        args_schema_summary={"date": "Optional ISO date filter."},
    ),
    ToolDefinition(
        id="calendar.create_event",
        namespace="calendar",
        label="Create calendar event",
        risk_hints=("writes_calendar", "external_attendee"),
        args_schema_summary={
            "title": "Event title.",
            "attendees": "List of attendee email addresses.",
            "start": "ISO timestamp.",
            "duration_minutes": "Event duration.",
        },
        replay_safe=False,
    ),
    ToolDefinition(
        id="files.read",
        namespace="files",
        label="Read file",
        risk_hints=("reads_local_file", "sensitive_file"),
        args_schema_summary={"path": "Path inside the deterministic mock workspace."},
    ),
    ToolDefinition(
        id="files.write",
        namespace="files",
        label="Write file",
        risk_hints=("writes_local_file", "destructive_change"),
        args_schema_summary={"path": "Path inside the deterministic mock workspace.", "content": "Text content."},
        replay_safe=False,
    ),
    ToolDefinition(
        id="github.create_issue",
        namespace="github",
        label="Create GitHub issue",
        risk_hints=("external_side_effect",),
        args_schema_summary={"repo": "Repository slug.", "title": "Issue title.", "body": "Issue body."},
        replay_safe=False,
    ),
    ToolDefinition(
        id="github.push_branch",
        namespace="github",
        label="Push branch",
        risk_hints=("code_publication", "force_push"),
        args_schema_summary={"repo": "Repository slug.", "branch": "Branch name.", "force": "Whether to force push."},
        replay_safe=False,
    ),
    ToolDefinition(
        id="browser.open",
        namespace="browser",
        label="Open URL",
        risk_hints=("reads_remote_content", "prompt_injection_source"),
        args_schema_summary={"url": "URL to open in the deterministic browser fixture."},
    ),
    ToolDefinition(
        id="browser.extract_text",
        namespace="browser",
        label="Extract page text",
        risk_hints=("reads_remote_content", "prompt_injection_source"),
        args_schema_summary={"url": "URL to read from the deterministic browser fixture."},
    ),
    ToolDefinition(
        id="shell.run",
        namespace="shell",
        label="Run shell command",
        risk_hints=("local_execution", "destructive_command"),
        args_schema_summary={"cmd": "Allowlisted shell command string."},
        replay_safe=False,
    ),
)

_TOOL_BY_ID = {tool.id: tool for tool in ALL_TOOLS}


def get_tool(tool_id: str) -> ToolDefinition:
    try:
        return _TOOL_BY_ID[tool_id]
    except KeyError as exc:
        raise KeyError(f"Unknown tool '{tool_id}'.") from exc


def supported_tools() -> set[str]:
    return set(_TOOL_BY_ID)


def tools_by_namespace(namespace: str) -> tuple[ToolDefinition, ...]:
    return tuple(tool for tool in ALL_TOOLS if tool.namespace == namespace)


def namespace_map() -> dict[str, tuple[ToolDefinition, ...]]:
    namespaces = sorted({tool.namespace for tool in ALL_TOOLS})
    return {namespace: tools_by_namespace(namespace) for namespace in namespaces}


def manifest_for_json() -> list[dict[str, Any]]:
    return [
        {
            "id": tool.id,
            "namespace": tool.namespace,
            "label": tool.label,
            "risk_hints": list(tool.risk_hints),
            "args_schema_summary": tool.args_schema_summary,
            "replay_safe": tool.replay_safe,
        }
        for tool in ALL_TOOLS
    ]


DISPATCH: dict[str, AdapterCallable] = {}
