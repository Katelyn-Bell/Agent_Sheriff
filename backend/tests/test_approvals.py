from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.approvals.queue import ApprovalQueue, redact_args
from agentsheriff.approvals.service import ApprovalService
from agentsheriff.config import Settings
from agentsheriff.models.dto import ApprovalState, ToolCallRequest
from agentsheriff.models.orm import Approval, Base


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return Session()


def _session_factory(database_url: str = "sqlite:///:memory:"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _request() -> ToolCallRequest:
    return ToolCallRequest(
        agent_id="a1",
        tool="gmail.send_email",
        args={"to": "team@example.com", "body": "hello"},
        context={},
    )


def test_resolve_approve_updates_state_and_fires_event() -> None:
    session = _session()
    queue = ApprovalQueue(session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=120)

    from agentsheriff.approvals.queue import _approval_events
    assert approval.id in _approval_events
    event = _approval_events[approval.id]

    resolved = queue.resolve(approval.id, "approve")
    assert resolved.state == ApprovalState.approved
    assert event.is_set()
    session.close()


def test_resolve_deny_updates_state_and_fires_event() -> None:
    session = _session()
    queue = ApprovalQueue(session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=120)

    resolved = queue.resolve(approval.id, "deny")
    assert resolved.state == ApprovalState.denied
    session.close()


def test_resolve_redact_updates_state_and_fires_event() -> None:
    session = _session()
    queue = ApprovalQueue(session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=120)

    resolved = queue.resolve(approval.id, "redact")
    assert resolved.state == ApprovalState.redacted
    session.close()


def test_redact_args_scrubs_sensitive_keys() -> None:
    args = {"to": "team@example.com", "body": "secret payload", "attachments": ["invoice.pdf"], "subject": "Hello"}
    result = redact_args(args)
    assert result["to"] == "team@example.com"
    assert result["body"] == "[REDACTED]"
    assert result["attachments"] == []
    assert result["subject"] == "Hello"


def test_await_resolution_unblocks_on_resolve() -> None:
    session = _session()
    queue = ApprovalQueue(session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=10)

    async def _drive() -> ApprovalState:
        async def _resolver():
            await asyncio.sleep(0.05)
            queue.resolve(approval.id, "approve")

        asyncio.create_task(_resolver())
        resolved = await queue.await_resolution(approval.id, timeout_s=5)
        return resolved.state

    state = asyncio.run(_drive())
    assert state == ApprovalState.approved
    session.close()


def test_await_resolution_unblocks_when_resolved_from_thread(tmp_path) -> None:
    Session = _session_factory(f"sqlite:///{tmp_path / 'approvals.db'}")
    waiting_session = Session()
    resolving_session = Session()
    queue = ApprovalQueue(waiting_session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=10)

    async def _drive() -> ApprovalState:
        async def _resolver():
            await asyncio.sleep(0.05)
            await asyncio.to_thread(ApprovalQueue(resolving_session).resolve, approval.id, "approve")

        asyncio.create_task(_resolver())
        resolved = await asyncio.wait_for(queue.await_resolution(approval.id, timeout_s=5), timeout=1)
        return resolved.state

    state = asyncio.run(_drive())
    assert state == ApprovalState.approved
    resolving_session.close()
    waiting_session.close()


def test_await_resolution_times_out() -> None:
    session = _session()
    queue = ApprovalQueue(session)
    approval = queue.create_pending(request=_request(), reason="Needs review", policy_version_id="pv_1", timeout_s=1)

    async def _drive() -> ApprovalState:
        resolved = await queue.await_resolution(approval.id, timeout_s=1)
        return resolved.state

    state = asyncio.run(_drive())
    assert state == ApprovalState.timed_out
    session.close()


def test_expired_approval_sets_timed_out() -> None:
    session = _session()
    request = ToolCallRequest(agent_id="a1", tool="gmail.send_email", args={"to": "team@example.com"}, context={})
    approval = ApprovalQueue(session).create_pending(
        request=request, reason="Needs review", policy_version_id="pv_1", timeout_s=120
    )
    row = session.get(Approval, approval.id)
    assert row is not None
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()

    expired = ApprovalQueue(session).expire_pending()
    session.close()

    assert expired[0].state == ApprovalState.timed_out
