from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from agentsheriff.models.dto import AuditEntryDTO, Decision

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("", response_model=list[AuditEntryDTO])
def list_audit(
    limit: int = 50,
    agent_id: str | None = None,
    decision: Decision | None = None,
    policy_version_id: str | None = None,
    since: str | None = None,
) -> list[AuditEntryDTO]:
    _ = (limit, agent_id, decision, policy_version_id, since)
    return [
        AuditEntryDTO(
            id="audit_stub",
            ts=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            agent_id="deputy-dusty",
            agent_label="Deputy Dusty",
            tool="calendar.create_event",
            args={"title": "Town hall"},
            context={"task_id": "stub-task"},
            decision=Decision.allow,
            risk_score=10,
            reason="Stub audit row for frontend integration.",
            matched_rule_id="stub.allow",
            judge_used=False,
            judge_rationale=None,
            policy_version_id="pv_stub",
            approval_id=None,
            execution_summary={"status": "stubbed"},
            user_explanation=None,
        )
    ]
