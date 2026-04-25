from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import AuditEntryDTO, Decision, ToolCallRequest
from agentsheriff.models.orm import AuditEntry
from agentsheriff.policy.store import utc_iso


class AuditStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        request: ToolCallRequest,
        decision: Decision,
        risk_score: int,
        reason: str,
        matched_rule_id: str | None,
        judge_used: bool,
        judge_rationale: str | None,
        policy_version_id: str,
        heuristic_summary: dict,
        approval_id: str | None = None,
        execution_summary: dict | None = None,
        user_explanation: str | None = None,
    ) -> AuditEntryDTO:
        row = AuditEntry(
            id=f"audit_{uuid4().hex[:12]}",
            agent_id=request.agent_id,
            agent_label=request.agent_label,
            tool=request.tool,
            args=request.args,
            context=request.context.model_dump(mode="json"),
            heuristic_summary=heuristic_summary,
            decision=decision.value,
            risk_score=risk_score,
            reason=reason,
            matched_rule_id=matched_rule_id,
            judge_used=judge_used,
            judge_rationale=judge_rationale,
            policy_version_id=policy_version_id,
            approval_id=approval_id,
            execution_summary=execution_summary,
            user_explanation=user_explanation,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def list_entries(
        self,
        *,
        limit: int = 50,
        agent_id: str | None = None,
        decision: Decision | None = None,
        policy_version_id: str | None = None,
        since: str | None = None,
    ) -> list[AuditEntryDTO]:
        _ = since
        statement = select(AuditEntry).order_by(AuditEntry.ts.desc()).limit(limit)
        if agent_id:
            statement = statement.where(AuditEntry.agent_id == agent_id)
        if decision:
            statement = statement.where(AuditEntry.decision == decision.value)
        if policy_version_id:
            statement = statement.where(AuditEntry.policy_version_id == policy_version_id)
        return [self.to_dto(row) for row in self.session.scalars(statement).all()]

    @staticmethod
    def to_dto(row: AuditEntry) -> AuditEntryDTO:
        return AuditEntryDTO(
            id=row.id,
            ts=utc_iso(row.ts) or "",
            agent_id=row.agent_id,
            agent_label=row.agent_label,
            tool=row.tool,
            args=row.args,
            context=row.context,
            decision=Decision(row.decision),
            risk_score=row.risk_score,
            reason=row.reason,
            matched_rule_id=row.matched_rule_id,
            judge_used=row.judge_used,
            judge_rationale=row.judge_rationale,
            policy_version_id=row.policy_version_id,
            approval_id=row.approval_id,
            execution_summary=row.execution_summary,
            user_explanation=row.user_explanation,
        )
