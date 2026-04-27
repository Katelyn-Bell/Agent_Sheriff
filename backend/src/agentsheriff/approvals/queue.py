from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import ApprovalDTO, ApprovalState, ToolCallRequest
from agentsheriff.models.orm import Approval
from agentsheriff.policy.store import utc_iso

# Module-level event store: approval_id -> asyncio.Event
_approval_events: dict[str, asyncio.Event] = {}
_approval_event_loops: dict[str, asyncio.AbstractEventLoop] = {}


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
        user_explanation: str | None = None,
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
            user_explanation=user_explanation,
            created_at=now,
            expires_at=now + timedelta(seconds=timeout_s),
            policy_version_id=policy_version_id,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        _approval_events[row.id] = asyncio.Event()
        _approval_event_loops[row.id] = _current_loop()
        return self.to_dto(row)

    async def await_resolution(self, approval_id: str, timeout_s: int) -> ApprovalDTO:
        event = _approval_events.get(approval_id)
        if event is None:
            row = self.session.get(Approval, approval_id)
            return self.to_dto(row) if row else _missing_approval(approval_id)

        timed_out = False
        try:
            await asyncio.wait_for(asyncio.shield(event.wait()), timeout=float(timeout_s))
        except asyncio.TimeoutError:
            timed_out = True
        finally:
            _approval_events.pop(approval_id, None)
            _approval_event_loops.pop(approval_id, None)

        self.session.expire_all()
        row = self.session.get(Approval, approval_id)
        if timed_out and row and row.state == ApprovalState.pending.value:
            row.state = ApprovalState.timed_out.value
            self.session.commit()
            self.session.refresh(row)
        return self.to_dto(row) if row else _missing_approval(approval_id)

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
        dto = self.to_dto(row)
        _notify_event(approval_id)
        return dto

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
                event = _approval_events.pop(row.id, None)
                if event is not None:
                    _notify_event(row.id, event=event)
                    _approval_event_loops.pop(row.id, None)
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
            user_explanation=getattr(row, "user_explanation", None),
            created_at=utc_iso(row.created_at) or "",
            expires_at=utc_iso(row.expires_at) or "",
            policy_version_id=row.policy_version_id,
        )


def _missing_approval(approval_id: str) -> ApprovalDTO:
    now = datetime.now(timezone.utc).isoformat()
    return ApprovalDTO(
        id=approval_id,
        state=ApprovalState.timed_out,
        agent_id="unknown",
        tool="unknown",
        args={},
        reason="Approval record not found.",
        created_at=now,
        expires_at=now,
        policy_version_id="unknown",
    )


def _current_loop() -> asyncio.AbstractEventLoop | None:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def _notify_event(approval_id: str, event: asyncio.Event | None = None) -> None:
    event = event or _approval_events.get(approval_id)
    if event is None:
        return

    loop = _approval_event_loops.get(approval_id)
    if loop is not None and loop.is_running():
        if _current_loop() is loop:
            event.set()
        else:
            loop.call_soon_threadsafe(event.set)
        return

    event.set()


def redact_args(args: dict[str, Any]) -> dict[str, Any]:
    _SENSITIVE_KEYS = {"body", "message", "content", "source_content", "attachments"}
    redacted: dict[str, Any] = {}
    for key, value in args.items():
        if key in _SENSITIVE_KEYS:
            redacted[key] = [] if isinstance(value, list) else ({} if isinstance(value, dict) else "[REDACTED]")
        elif isinstance(value, dict):
            redacted[key] = redact_args(value)
        else:
            redacted[key] = value
    return redacted
