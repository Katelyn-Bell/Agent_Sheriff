from __future__ import annotations

import asyncio

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

    response = asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="calendar.create_event", args={"title": "Sync"}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    ))
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

    response = asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="github.push_branch", args={"force": True}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    ))
    session.close()

    assert response.decision == Decision.deny
    assert response.risk_score == 90
    assert response.judge_used is False


def test_gateway_jail_on_deny() -> None:
    session, policy_store, audit_store = _stores()
    agent_store = AgentStore(session)
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(
        name="test",
        static_rules=[StaticRuleDTO(
            id="deny_and_jail",
            name="Deny and jail",
            tool_match=ToolMatchDTO(kind="exact", value="shell.run"),
            action=RuleAction.deny,
            jail_on_deny=True,
            reason="Destructive shell blocked.",
        )],
    )).id)

    asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="agent_bad", tool="shell.run", args={"command": "rm -rf /"}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        agent_store=agent_store,
        settings=_settings(),
    ))
    agents = agent_store.list()
    session.close()

    assert agents[0].id == "agent_bad"
    assert agents[0].state == "jailed"


def test_gateway_delegates_unresolved_call_to_judge() -> None:
    session, policy_store, audit_store = _stores()
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(name="test")).id)

    response = asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="gmail.send_email", args={"to": "team@example.com"}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    ))
    session.close()

    assert response.decision == Decision.allow
    assert response.judge_used is True
    assert response.matched_rule_id is None


def test_gateway_denies_unknown_tool() -> None:
    session, policy_store, audit_store = _stores()
    response = asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="a1", tool="unknown.tool", args={}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        settings=_settings(),
    ))
    session.close()

    assert response.decision == Decision.deny
    assert response.policy_version_id == "pv_unvalidated"


def test_gateway_approval_blocks_then_resolves() -> None:
    session, policy_store, audit_store = _stores()
    approval_queue = ApprovalQueue(session)
    policy_store.publish(policy_store.create_draft(PolicyCreateRequest(
        name="test",
        static_rules=[StaticRuleDTO(
            id="approve_email",
            name="Approve email",
            tool_match=ToolMatchDTO(kind="exact", value="gmail.send_email"),
            action=RuleAction.require_approval,
            reason="Needs human review.",
        )],
    )).id)

    request = ToolCallRequest(
        agent_id="a1",
        tool="gmail.send_email",
        args={"to": "accountant@example.com", "body": "Please review"},
        context={},
    )

    async def _run() -> Decision:
        async def _resolver():
            await asyncio.sleep(0.05)
            pending = approval_queue.list()
            if pending:
                approval_queue.resolve(pending[0].id, "approve")

        call_task = asyncio.create_task(handle_tool_call(
            request,
            policy_store=policy_store,
            audit_store=audit_store,
            approval_queue=approval_queue,
            settings=Settings(GATEWAY_ADAPTER_SECRET="test-secret", APPROVAL_TIMEOUT_S=5),
        ))
        asyncio.create_task(_resolver())
        response = await call_task
        return response.decision

    decision = asyncio.run(_run())
    session.close()

    assert decision == Decision.allow


def test_gateway_upserts_agent_state() -> None:
    session, policy_store, audit_store = _stores()
    agent_store = AgentStore(session)

    asyncio.run(handle_tool_call(
        ToolCallRequest(agent_id="a1", agent_label="Deputy One", tool="gmail.read_inbox", args={}, context={}),
        policy_store=policy_store,
        audit_store=audit_store,
        agent_store=agent_store,
        settings=_settings(),
    ))
    agents = agent_store.list()
    session.close()

    assert len(agents) == 1
    assert agents[0].id == "a1"
    assert agents[0].label == "Deputy One"
    assert agents[0].state == "active"
