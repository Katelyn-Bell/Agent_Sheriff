from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from agentsheriff.main import app
from agentsheriff.models.orm import Base


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


def test_policy_api_create_publish_archive_contract(client: TestClient) -> None:
    create_response = client.post("/v1/policies", json={"name": "API policy"})
    assert create_response.status_code == 200
    policy = create_response.json()

    publish_response = client.post(f"/v1/policies/{policy['id']}/publish")
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    archive_response = client.post(f"/v1/policies/{policy['id']}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"


def test_policy_generate_returns_frontend_usable_rules(client: TestClient) -> None:
    response = client.post("/v1/policies/generate", json={
        "name": "Finance assistant",
        "user_intent": "Send finance updates and read inbox.",
        "tool_manifest": ["gmail.read_inbox", "gmail.send_email", "github.push_branch"],
    })

    assert response.status_code == 200
    rule_ids = {rule["id"] for rule in response.json()["static_rules"]}
    assert "policy.generated.allow_gmail_read_inbox" in rule_ids
    assert "policy.generated.review_email_attachments" in rule_ids
    assert "policy.generated.block_force_push" in rule_ids


def test_tools_api_returns_canonical_manifest(client: TestClient) -> None:
    response = client.get("/v1/tools")

    assert response.status_code == 200
    tools = {tool["id"]: tool for tool in response.json()}
    assert "gmail.send_email" in tools
    assert tools["gmail.send_email"]["namespace"] == "gmail"
    assert "external_recipient" in tools["gmail.send_email"]["risk_hints"]
    assert tools["calendar.create_event"]["replay_safe"] is False


def test_gateway_audit_and_eval_api_contract(client: TestClient) -> None:
    policy = client.post("/v1/policies", json={
        "name": "API policy",
        "static_rules": [{
            "id": "deny_shell",
            "name": "Deny shell",
            "tool_match": {"kind": "namespace", "value": "shell"},
            "action": "deny",
            "reason": "Shell is blocked.",
        }],
    }).json()

    call_response = client.post("/v1/tool-call", json={
        "agent_id": "a1",
        "tool": "shell.run",
        "args": {"cmd": "ls"},
        "context": {"task_id": "api-contract"},
    })
    assert call_response.status_code == 200
    assert call_response.json()["decision"] == "allow"

    eval_response = client.post("/v1/evals", json={"policy_version_id": policy["id"], "filters": {"agent_id": "a1"}})
    assert eval_response.status_code == 200
    eval_run = eval_response.json()

    completed = client.get(f"/v1/evals/{eval_run['id']}").json()
    results = client.get(f"/v1/evals/{eval_run['id']}/results").json()
    audit_rows = client.get("/v1/audit", params={"agent_id": "a1", "limit": 10}).json()

    assert completed["status"] == "completed"
    assert completed["disagreed"] == 1
    assert results[0]["replayed_decision"] == "deny"
    assert audit_rows[0]["heuristic_summary"]["risk_score"] >= 0


def test_api_uses_error_envelope_for_missing_eval(client: TestClient) -> None:
    response = client.get("/v1/evals/missing")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Eval run not found."}}
