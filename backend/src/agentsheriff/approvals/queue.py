from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import ApprovalDTO, ApprovalState, ToolCallRequest
from agentsheriff.models.orm import Approval
from agentsheriff.policy.store import utc_iso


class ApprovalQueue:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_pending(
        self,
        *,
        request: ToolCallRequest,
        reason: str,
        policy_version_id: str,
        timeout_s: int,
    ) -> ApprovalDTO:
        now = datetime.now(timezone.utc)
        row = Approval(
            id=f"approval_{uuid4().hex[:12]}",
            state=ApprovalState.pending.value,
            agent_id=request.agent_id,
            agent_label=request.agent_label,
            tool=request.tool,
            args=request.args,
            reason=reason,
            created_at=now,
            expires_at=now + timedelta(seconds=timeout_s),
            policy_version_id=policy_version_id,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def list(self, state: ApprovalState | None = ApprovalState.pending) -> list[ApprovalDTO]:
        self.expire_pending()
        statement = select(Approval).order_by(Approval.created_at.desc())
        if state is not None:
            statement = statement.where(Approval.state == state.value)
        return [self.to_dto(row) for row in self.session.scalars(statement).all()]

    def resolve(self, approval_id: str, action: str) -> ApprovalDTO:
        self.expire_pending()
        row = self.session.get(Approval, approval_id)
        if row is None:
            raise KeyError(approval_id)
        if row.state != ApprovalState.pending.value:
            raise ValueError("Only pending approvals can be resolved.")
        row.state = {
            "approve": ApprovalState.approved.value,
            "deny": ApprovalState.denied.value,
            "redact": ApprovalState.redacted.value,
        }[action]
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def expire_pending(self) -> list[ApprovalDTO]:
        now = datetime.now(timezone.utc)
        rows = self.session.scalars(
            select(Approval).where(Approval.state == ApprovalState.pending.value, Approval.expires_at <= now)
        ).all()
        for row in rows:
            row.state = ApprovalState.timed_out.value
        if rows:
            self.session.commit()
            for row in rows:
                self.session.refresh(row)
        return [self.to_dto(row) for row in rows]

    @staticmethod
    def to_dto(row: Approval) -> ApprovalDTO:
        return ApprovalDTO(
            id=row.id,
            state=ApprovalState(row.state),
            agent_id=row.agent_id,
            agent_label=row.agent_label,
            tool=row.tool,
            args=row.args,
            reason=row.reason,
            created_at=utc_iso(row.created_at) or "",
            expires_at=utc_iso(row.expires_at) or "",
            policy_version_id=row.policy_version_id,
        )
