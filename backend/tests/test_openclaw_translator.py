from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentsheriff.main import app
from agentsheriff.models.orm import Base
from agentsheriff.openclaw import OpenClawCallEnvelope, translate_openclaw_call


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    original_factory = app.state.session_factory
    app.state.session_factory = SessionLocal
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.session_factory = original_factory


def test_translator_emits_skill_id_in_context() -> None:
    request = translate_openclaw_call(OpenClawCallEnvelope(
        conversation_id="conv-crypto",
        task_id="task-1",
        prompt="What Kalshi markets are open in the Crypto category?",
        tool_call={
            "tool": "shell.run",
            "args": {"command": "kalshi-cli markets list --category Crypto"},
        },
    ))

    assert request.context.skill_id == "kalshi-trading"
    assert request.context.conversation_id == "conv-crypto"
    assert request.context.source_prompt == "What Kalshi markets are open in the Crypto category?"


def test_translator_maps_kalshi_orders_create_to_shell_run() -> None:
    request = translate_openclaw_call({
        "conversation_id": "conv-order",
        "tool_call": {
            "name": "kalshi.orders_create",
            "arguments": {
                "market": "KXBTC-26FEB12-B97000",
                "side": "yes",
                "qty": 10,
                "price": 50,
            },
        },
    })

    assert request.tool == "shell.run"
    assert request.args["command"].startswith("kalshi-cli orders create")
    assert request.args["cmd"] == request.args["command"]
    assert "--market KXBTC-26FEB12-B97000" in request.args["command"]
    assert "--side yes" in request.args["command"]


def test_translator_preserves_agent_id_across_calls() -> None:
    first = translate_openclaw_call({
        "conversation_id": "same-conversation",
        "args": {"command": "kalshi-cli markets list"},
    })
    second = translate_openclaw_call({
        "conversation_id": "same-conversation",
        "args": {"command": "kalshi-cli portfolio balance"},
    })

    assert first.agent_id == "openclaw_kalshi"
    assert second.agent_id == first.agent_id
    assert second.agent_label == "Kalshi Trader"


def test_translator_preserves_generic_openclaw_shell_command() -> None:
    request = translate_openclaw_call({
        "conversation_id": "shell-conversation",
        "tool_call": {
            "tool": "exec",
            "args": {"command": "echo hello"},
        },
    })

    assert request.tool == "shell.run"
    assert request.args["command"] == "echo hello"
    assert request.context.skill_id == "openclaw-shell"


def test_openclaw_endpoint_forwards_to_gateway_and_returns_decision(client: TestClient) -> None:
    policy = client.post("/v1/policies", json={
        "name": "OpenClaw Kalshi guard",
        "static_rules": [{
            "id": "deny_openclaw_prod",
            "name": "Deny OpenClaw prod",
            "tool_match": {"kind": "exact", "value": "shell.run"},
            "skill_match": {"kind": "exact", "value": "kalshi-trading"},
            "arg_predicates": [{"path": "cmd", "operator": "contains", "value": "--prod"}],
            "action": "deny",
            "reason": "Production Kalshi calls are blocked.",
        }],
    }).json()
    client.post(f"/v1/policies/{policy['id']}/publish")

    response = client.post("/v1/openclaw/tool-call", json={
        "conversation_id": "conv-prod",
        "task_id": "task-prod",
        "prompt": "Place the production order.",
        "tool_call": {
            "tool": "shell.run",
            "args": {
                "command": "kalshi-cli --prod orders create --market KXBTC-26FEB12-B97000 --side yes --qty 10 --price 50"
            },
        },
    })

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["blocked"] is True
    assert payload["decision"] == "deny"
    assert payload["agentsheriff"]["decision"] == "deny"
    assert payload["agentsheriff"]["matched_rule_id"] == "deny_openclaw_prod"
