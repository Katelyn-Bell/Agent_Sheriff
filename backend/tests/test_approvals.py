from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.approvals.service import ApprovalService
from agentsheriff.audit.store import AuditStore
from agentsheriff.config import Settings
from agentsheriff.models.dto import ApprovalState, Decision, ToolCallRequest
from agentsheriff.models.orm import Approval, Base


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return Session()


def test_approved_request_executes_adapter_and_updates_audit() -> None:
    session = _session()
    request = ToolCallRequest(
        agent_id="a1",
        tool="gmail.send_email",
        args={"to": "team@example.com", "body": "hello"},
        context={},
    )
    approval = ApprovalQueue(session).create_pending(
        request=request,
        reason="Needs review",
        policy_version_id="pv_1",
        timeout_s=120,
    )
    AuditStore(session).record(
        request=request,
        decision=Decision.approval_required,
        risk_score=60,
        reason="Needs review",
        matched_rule_id="approval_rule",
        judge_used=False,
        judge_rationale=None,
        policy_version_id="pv_1",
        heuristic_summary={"risk_score": 60, "signals": []},
        approval_id=approval.id,
    )

    resolved = ApprovalService(session, Settings(GATEWAY_ADAPTER_SECRET="test")).resolve(approval.id, "approve")
    audit = AuditStore(session).list_entries()[0]
    session.close()

    assert resolved.state == ApprovalState.approved
    assert audit.decision == Decision.allow
    assert audit.execution_summary is not None
    assert audit.execution_summary["status"] == "ok"
    assert audit.execution_summary["tool"] == "gmail.send_email"
    assert audit.execution_summary["to"] == "team@example.com"
    assert audit.execution_summary["body_preview"] == "hello"


def test_redacted_request_scrubs_sensitive_args_before_execution() -> None:
    session = _session()
    request = ToolCallRequest(
        agent_id="a1",
        tool="gmail.send_email",
        args={"to": "team@example.com", "body": "secret", "attachments": ["invoice.pdf"]},
        context={},
    )
    approval = ApprovalQueue(session).create_pending(
        request=request,
        reason="Needs review",
        policy_version_id="pv_1",
        timeout_s=120,
    )
    AuditStore(session).record(
        request=request,
        decision=Decision.approval_required,
        risk_score=60,
        reason="Needs review",
        matched_rule_id="approval_rule",
        judge_used=False,
        judge_rationale=None,
        policy_version_id="pv_1",
        heuristic_summary={"risk_score": 60, "signals": []},
        approval_id=approval.id,
    )

    resolved = ApprovalService(session, Settings(GATEWAY_ADAPTER_SECRET="test")).resolve(approval.id, "redact")
    audit = AuditStore(session).list_entries()[0]
    session.close()

    assert resolved.state == ApprovalState.redacted
    assert resolved.args == {"to": "team@example.com", "body": "[REDACTED]", "attachments": []}
    assert audit.decision == Decision.allow
    assert audit.args == resolved.args
    assert audit.execution_summary is not None
    assert audit.execution_summary["status"] == "ok"
    assert audit.execution_summary["tool"] == "gmail.send_email"
    assert audit.execution_summary["body_preview"] == "[REDACTED]"
    assert audit.execution_summary["attachments"] == []


def test_expired_approval_updates_audit_as_denied() -> None:
    session = _session()
    request = ToolCallRequest(agent_id="a1", tool="gmail.send_email", args={"to": "team@example.com"}, context={})
    approval = ApprovalQueue(session).create_pending(
        request=request,
        reason="Needs review",
        policy_version_id="pv_1",
        timeout_s=120,
    )
    row = session.get(Approval, approval.id)
    assert row is not None
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()
    AuditStore(session).record(
        request=request,
        decision=Decision.approval_required,
        risk_score=60,
        reason="Needs review",
        matched_rule_id="approval_rule",
        judge_used=False,
        judge_rationale=None,
        policy_version_id="pv_1",
        heuristic_summary={"risk_score": 60, "signals": []},
        approval_id=approval.id,
    )

    expired = ApprovalService(session, Settings(GATEWAY_ADAPTER_SECRET="test")).expire_pending()
    audit = AuditStore(session).list_entries()[0]
    session.close()

    assert expired[0].state == ApprovalState.timed_out
    assert audit.decision == Decision.deny
    assert audit.execution_summary == {"status": "not_executed", "approval_state": "timed_out"}
