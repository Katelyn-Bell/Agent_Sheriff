from __future__ import annotations

import json
import re
import shlex
from typing import Any

from agentsheriff.models.dto import Decision, ToolCallRequest, ToolCallResponse
from agentsheriff.openclaw.envelope import OpenClawCallEnvelope, OpenClawToolCallResult


KALSHI_SKILL_ID = "kalshi-trading"
OPENCLAW_SHELL_SKILL_ID = "openclaw-shell"
OPENCLAW_AGENT_ID = "openclaw_kalshi"
OPENCLAW_AGENT_LABEL = "Kalshi Trader"
KALSHI_BASE_COMMAND = "kalshi-cli"

_NESTED_CALL_KEYS = ("tool_call", "toolCall", "call", "action", "invocation", "request")
_TOOL_KEYS = ("tool", "tool_name", "name", "function_name")
_ARGS_KEYS = ("args", "arguments", "input", "parameters")
_COMMAND_KEYS = ("command", "cmd", "shell", "query")
_CONTEXT_KEYS = ("context", "metadata", "meta")


def translate_openclaw_call(envelope: OpenClawCallEnvelope | dict[str, Any]) -> ToolCallRequest:
    native = _as_dict(envelope)
    call = _tool_call_payload(native)
    args = _coerce_args(_first_present(call, _ARGS_KEYS))
    tool_name = _first_text(call, _TOOL_KEYS) or _first_text(native, _TOOL_KEYS)
    context = _context_payload(native, call)
    command = _shell_command(native=native, call=call, args=args, tool_name=tool_name)

    task_id = _first_text(context, ("task_id", "taskId")) or _first_text(call, ("id", "call_id", "callId")) or _first_text(
        native, ("task_id", "taskId", "id", "call_id", "callId")
    )
    conversation_id = _first_text(context, ("conversation_id", "conversationId", "thread_id", "threadId")) or _first_text(
        native, ("conversation_id", "conversationId", "thread_id", "threadId")
    )
    source_prompt = _first_text(context, ("source_prompt", "sourcePrompt", "prompt", "user_prompt", "userPrompt")) or _first_text(
        native, ("source_prompt", "sourcePrompt", "prompt", "user_prompt", "userPrompt")
    )
    source_content = _first_text(context, ("source_content", "sourceContent", "content", "document", "research_note")) or _first_text(
        native, ("source_content", "sourceContent", "content", "document", "research_note")
    )

    skill_id = (
        _first_text(context, ("skill_id", "skillId"))
        or (KALSHI_SKILL_ID if _is_kalshi_command(command) or _is_kalshi_tool_name(tool_name) else OPENCLAW_SHELL_SKILL_ID)
    )

    request_context = {
        "task_id": task_id,
        "source_prompt": source_prompt,
        "source_content": source_content,
        "conversation_id": conversation_id,
        "skill_id": skill_id,
    }

    return ToolCallRequest(
        agent_id=OPENCLAW_AGENT_ID,
        agent_label=OPENCLAW_AGENT_LABEL,
        tool="shell.run",
        # `command` is the OpenClaw bridge contract; `cmd` keeps existing
        # AgentSheriff shell policies and demo adapters effective.
        args={"command": command, "cmd": command},
        context={key: value for key, value in request_context.items() if value is not None},
    )


def translate_tool_call_response(response: ToolCallResponse) -> OpenClawToolCallResult:
    agentsheriff_payload = response.model_dump(mode="json")
    return OpenClawToolCallResult(
        ok=response.decision == Decision.allow,
        decision=response.decision.value,
        reason=response.reason,
        blocked=response.decision == Decision.deny,
        approval_required=response.decision == Decision.approval_required,
        audit_id=response.audit_id,
        approval_id=response.approval_id,
        result=response.result,
        agentsheriff=agentsheriff_payload,
    )


def _as_dict(envelope: OpenClawCallEnvelope | dict[str, Any]) -> dict[str, Any]:
    if isinstance(envelope, OpenClawCallEnvelope):
        return envelope.model_dump(mode="python", exclude_none=True)
    return dict(envelope)


def _tool_call_payload(native: dict[str, Any]) -> dict[str, Any]:
    for key in _NESTED_CALL_KEYS:
        value = native.get(key)
        if isinstance(value, dict):
            return value
    return native


def _context_payload(native: dict[str, Any], call: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in (native, call):
        for key in _CONTEXT_KEYS:
            value = source.get(key)
            if isinstance(value, dict):
                merged.update(value)
    return merged


def _shell_command(
    *,
    native: dict[str, Any],
    call: dict[str, Any],
    args: dict[str, Any],
    tool_name: str | None,
) -> str:
    command = _first_text(args, _COMMAND_KEYS) or _first_text(call, _COMMAND_KEYS) or _first_text(native, _COMMAND_KEYS)
    if command:
        return _normalize_command(command, tool_name)

    argv = args.get("argv") or args.get("command_argv") or args.get("commandArgv")
    if isinstance(argv, list) and argv:
        return _normalize_command(" ".join(shlex.quote(str(part)) for part in argv), tool_name)

    subcommand = _subcommand_from_args(args) or _subcommand_from_tool_name(tool_name)
    if subcommand:
        return _structured_kalshi_command(subcommand, args)

    raise ValueError("OpenClaw payload did not include a Kalshi command, argv, or recognizable tool name.")


def _normalize_command(command: str, tool_name: str | None) -> str:
    normalized = command.strip()
    if not normalized:
        raise ValueError("OpenClaw payload included an empty command.")
    if _is_generic_shell_tool(tool_name):
        return normalized
    if normalized == KALSHI_BASE_COMMAND or normalized.startswith(f"{KALSHI_BASE_COMMAND} "):
        return normalized
    return f"{KALSHI_BASE_COMMAND} {normalized}"


def _is_generic_shell_tool(tool_name: str | None) -> bool:
    return (tool_name or "").strip().lower() in {"exec", "bash", "shell", "shell.run", "terminal", "terminal.run"}


def _is_kalshi_command(command: str) -> bool:
    return command.strip() == KALSHI_BASE_COMMAND or command.strip().startswith(f"{KALSHI_BASE_COMMAND} ")


def _is_kalshi_tool_name(tool_name: str | None) -> bool:
    return bool(tool_name) and (tool_name or "").strip().lower().replace("_", "-").startswith(("kalshi", "kalshi-cli"))


def _structured_kalshi_command(subcommand: str, args: dict[str, Any]) -> str:
    parts = [KALSHI_BASE_COMMAND, *shlex.split(subcommand)]
    skip_keys = {
        "argv",
        "command_argv",
        "commandArgv",
        "command",
        "cmd",
        "shell",
        "query",
        "subcommand",
        "sub_command",
        "subCommand",
    }
    for key, value in args.items():
        if key in skip_keys or value is None:
            continue
        flag = _flag_name(key)
        if isinstance(value, bool):
            if value:
                parts.append(flag)
            continue
        if isinstance(value, list):
            for item in value:
                parts.extend([flag, shlex.quote(str(item))])
            continue
        parts.extend([flag, shlex.quote(str(value))])
    return " ".join(parts)


def _subcommand_from_args(args: dict[str, Any]) -> str | None:
    return _first_text(args, ("subcommand", "sub_command", "subCommand"))


def _subcommand_from_tool_name(tool_name: str | None) -> str | None:
    if not tool_name:
        return None
    normalized = tool_name.strip()
    if normalized in {"shell.run", "shell", "bash"}:
        return None
    normalized = re.sub(r"^(kalshi|kalshi-cli|kalshi_cli)[._:-]?", "", normalized)
    normalized = normalized.replace("_", " ").replace(".", " ").replace("-", " ")
    normalized = " ".join(part for part in normalized.split() if part)
    return normalized or None


def _flag_name(key: str) -> str:
    cleaned = key.strip().replace("_", "-")
    return cleaned if cleaned.startswith("-") else f"--{cleaned}"


def _first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    value = _first_present(payload, keys)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _coerce_args(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return {"command": value}
        if isinstance(loaded, dict):
            return loaded
        return {"command": value}
    return {}
