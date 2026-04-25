from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import case, func, select
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
        until: str | None = None,
    ) -> list[AuditEntryDTO]:
        statement = select(AuditEntry).order_by(AuditEntry.ts.desc())
        if agent_id:
            statement = statement.where(AuditEntry.agent_id == agent_id)
        if decision:
            statement = statement.where(AuditEntry.decision == decision.value)
        if policy_version_id:
            statement = statement.where(AuditEntry.policy_version_id == policy_version_id)
        if since:
            statement = statement.where(AuditEntry.ts >= _parse_iso(since))
        if until:
            statement = statement.where(AuditEntry.ts <= _parse_iso(until))
        statement = statement.limit(limit)
        return [self.to_dto(row) for row in self.session.scalars(statement).all()]

    def get_by_id(self, audit_id: str) -> AuditEntryDTO | None:
        row = self.session.get(AuditEntry, audit_id)
        if row is None:
            return None
        self.session.refresh(row)
        return self.to_dto(row)

    def today_counters_for(self, agent_ids: list[str]) -> dict[str, dict[str, int]]:
        midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        rows = self.session.execute(
            select(
                AuditEntry.agent_id,
                func.count().label("requests_today"),
                func.sum(
                    case((AuditEntry.decision == Decision.deny.value, 1), else_=0)
                ).label("blocked_today"),
            )
            .where(AuditEntry.agent_id.in_(agent_ids), AuditEntry.ts >= midnight)
            .group_by(AuditEntry.agent_id)
        ).all()
        result: dict[str, dict[str, int]] = {aid: {"requests_today": 0, "blocked_today": 0} for aid in agent_ids}
        for row in rows:
            result[row.agent_id] = {
                "requests_today": row.requests_today or 0,
                "blocked_today": int(row.blocked_today or 0),
            }
        return result

    def apply_approval_resolution(
        self,
        *,
        approval_id: str,
        decision: Decision,
        reason: str,
        execution_summary: dict | None,
        args: dict | None = None,
        user_explanation: str | None = None,
    ) -> AuditEntryDTO | None:
        row = self.session.scalar(select(AuditEntry).where(AuditEntry.approval_id == approval_id))
        if row is None:
            return None
        row.decision = decision.value
        row.reason = reason
        row.execution_summary = execution_summary
        if args is not None:
            row.args = args
        if user_explanation is not None:
            row.user_explanation = user_explanation
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

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
            heuristic_summary=row.heuristic_summary,
            judge_used=row.judge_used,
            judge_rationale=row.judge_rationale,
            policy_version_id=row.policy_version_id,
            approval_id=row.approval_id,
            execution_summary=row.execution_summary,
            user_explanation=row.user_explanation,
        )


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
