from __future__ import annotations

from sqlalchemy.orm import Session

from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.models.dto import ApprovalDTO, ApprovalState
from agentsheriff.config import Settings


class ApprovalService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.queue = ApprovalQueue(session)

    def list(self, state: ApprovalState | None = ApprovalState.pending) -> list[ApprovalDTO]:
        self.queue.expire_pending()
        return self.queue.list(state)

    def resolve(self, approval_id: str, action: str) -> ApprovalDTO:
        return self.queue.resolve(approval_id, action)
