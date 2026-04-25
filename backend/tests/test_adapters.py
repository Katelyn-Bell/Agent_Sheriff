from __future__ import annotations

import pytest

from agentsheriff.adapters import ALL_TOOLS, DISPATCH, supported_tools
from agentsheriff.adapters._common import AdapterAuthError, AdapterValidationError


TOKEN = "test-secret"


def test_manifest_and_dispatch_are_complete() -> None:
    manifest_tools = {tool.id for tool in ALL_TOOLS}

    assert manifest_tools == supported_tools()
    assert manifest_tools == set(DISPATCH)
    assert {"gmail", "calendar", "files", "github", "browser", "shell"} <= {
        tool.namespace for tool in ALL_TOOLS
    }


def test_adapter_calls_require_gateway_token() -> None:
    with pytest.raises(AdapterAuthError):
        DISPATCH["gmail.send_email"](
            args={"to": "team@example.com", "subject": "No badge"},
            gateway_token="wrong-token",
        )


def test_scenario_critical_tools_have_deterministic_outputs() -> None:
    email_args = {
        "to": "accountant@external.example",
        "subject": "Draft invoice for review",
        "body": "Please review the attached invoice draft.",
        "attachments": ["invoice_draft.pdf"],
    }
    event_args = {
        "title": "Team trail check-in",
        "attendees": ["team@example.com"],
        "start": "2026-04-25T15:00:00-04:00",
        "duration_minutes": 30,
    }

    assert DISPATCH["gmail.send_email"](args=email_args, gateway_token=TOKEN) == DISPATCH["gmail.send_email"](
        args=email_args,
        gateway_token=TOKEN,
    )
    assert DISPATCH["calendar.create_event"](args=event_args, gateway_token=TOKEN) == DISPATCH[
        "calendar.create_event"
    ](args=event_args, gateway_token=TOKEN)
    assert DISPATCH["files.read"](args={"path": "invoices/invoice_draft.pdf"}, gateway_token=TOKEN) == DISPATCH[
        "files.read"
    ](args={"path": "invoices/invoice_draft.pdf"}, gateway_token=TOKEN)


def test_files_read_is_confined_to_mock_workspace() -> None:
    with pytest.raises(AdapterValidationError):
        DISPATCH["files.read"](args={"path": "../secrets.env"}, gateway_token=TOKEN)

    with pytest.raises(AdapterValidationError):
        DISPATCH["files.write"](args={"path": "/tmp/outside.txt", "content": "nope"}, gateway_token=TOKEN)


def test_shell_adapter_has_allowlisted_local_side_effects_only() -> None:
    result = DISPATCH["shell.run"](args={"cmd": "ls"}, gateway_token=TOKEN)

    assert result["stdout"] == "invoices\nnotes\nreadme.txt\n"
    with pytest.raises(AdapterValidationError):
        DISPATCH["shell.run"](args={"cmd": "rm -rf /"}, gateway_token=TOKEN)
