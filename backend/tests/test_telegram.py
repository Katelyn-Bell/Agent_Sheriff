from __future__ import annotations

from agentsheriff.notifications.telegram import parse_callback_data


def test_parse_callback_data_accepts_namespaced_agent_sheriff_payload() -> None:
    assert parse_callback_data("agentsheriff:approve:approval_abc123") == ("approve", "approval_abc123")


def test_parse_callback_data_accepts_plain_payload() -> None:
    assert parse_callback_data("deny:approval_abc123") == ("deny", "approval_abc123")


def test_parse_callback_data_rejects_unknown_payloads() -> None:
    assert parse_callback_data("other:approve:approval_abc123") is None
    assert parse_callback_data("agentsheriff:archive:approval_abc123") is None
