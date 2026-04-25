from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.agents import AgentStore
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.audit.store import AuditStore
from agentsheriff.config import Settings
from agentsheriff.gateway import handle_tool_call
from agentsheriff.models.dto import (
    Decision,
    PolicyCreateRequest,
    RuleAction,
    StaticRuleDTO,
    ToolCallRequest,
    ToolMatchDTO,
)
from agentsheriff.models.orm import Base
from agentsheriff.policy.store import PolicyStore


def _stores():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    return session, PolicyStore(session), AuditStore(session)


def _settings() -> Settings:
    return Settings(GATEWAY_ADAPTER_SECRET="test-secret")


def test_gateway_allows_via_static_rule() -> None:
    session, policy_store, audit_store = _stores()
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(
        name="test",
        static_rules=[StaticRuleDTO(
            id="allow_calendar",
            name="Allow calendar",
            tool_match=ToolMatchDTO(kind="exact", value="calendar.create_event"),
            action=RuleAction.allow,
            reason="Calendar events are allowed.",
        )],
    )).id)

    response = handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="calendar.create_event", args={"title": "Sync"}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    )
    session.close()

    assert response.decision == Decision.allow
    assert response.matched_rule_id == "allow_calendar"
    assert response.judge_used is False
    assert response.result is not None


def test_gateway_denies_via_static_rule() -> None:
    session, policy_store, audit_store = _stores()
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(
        name="test",
        static_rules=[StaticRuleDTO(
            id="deny_force_push",
            name="Deny force push",
            tool_match=ToolMatchDTO(kind="exact", value="github.push_branch"),
            action=RuleAction.deny,
            severity_floor=90,
            reason="Force pushes are blocked.",
        )],
    )).id)

    response = handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="github.push_branch", args={"force": True}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    )
    session.close()

    assert response.decision == Decision.deny
    assert response.risk_score == 90
    assert response.judge_used is False


def test_gateway_delegates_unresolved_call_to_judge() -> None:
    session, policy_store, audit_store = _stores()
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(name="test")).id)

    response = handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="gmail.send_email", args={"to": "team@example.com"}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    )
    session.close()

    assert response.decision == Decision.allow
    assert response.judge_used is True
    assert response.matched_rule_id is None


def test_gateway_denies_unknown_tool() -> None:
    session, policy_store, audit_store = _stores()
    response = handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="unknown.tool", args={}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    )
    session.close()

    assert response.decision == Decision.deny
    assert response.policy_version_id == "pv_unvalidated"


def test_gateway_creates_pending_approval_from_static_rule() -> None:
    session, policy_store, audit_store = _stores()
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(
        name="test",
        static_rules=[StaticRuleDTO(
            id="approve_attachment",
            name="Approve attachments",
            tool_match=ToolMatchDTO(kind="exact", value="gmail.send_email"),
            action=RuleAction.require_approval,
            reason="Attachments need review.",
        )],
    )).id)
    approval_queue = ApprovalQueue(session)

    response = handle_tool_call(
        ToolCallRequest(
            agent_id="a1",
            tool="gmail.send_email",
            args={"to": "accountant@example.com", "attachments": ["invoice.pdf"]},
            context={},
        ),
        policy_store=policy_store,
        audit_store=audit_store,
        approval_queue=approval_queue,
        settings=_settings(),
    )
    pending = approval_queue.list()
    session.close()

    assert response.decision == Decision.approval_required
    assert response.approval_id is not None
    assert len(pending) == 1
    assert pending[0].id == response.approval_id


def test_gateway_upserts_agent_state() -> None:
    session, policy_store, audit_store = _stores()
    agent_store = AgentStore(session)

    handle_tool_call(
        ToolCallRequest(agent_id="a1", agent_label="Deputy One", tool="gmail.read_inbox", args={}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        agent_store=agent_store,
        settings=_settings(),
    )
    agents = agent_store.list()
    session.close()

    assert agents == [{"id": "a1", "label": "Deputy One", "state": "active"}]
