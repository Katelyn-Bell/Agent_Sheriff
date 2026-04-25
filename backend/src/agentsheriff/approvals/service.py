from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from agentsheriff.adapters.manifest import DISPATCH
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.audit.store import AuditStore
from agentsheriff.config import Settings
from agentsheriff.models.dto import ApprovalDTO, ApprovalState, Decision


SENSITIVE_ARG_KEYS = {"body", "message", "content", "source_content", "attachments"}


class ApprovalService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.queue = ApprovalQueue(session)
        self.audit = AuditStore(session)

    def list(self, state: ApprovalState | None = ApprovalState.pending) -> list[ApprovalDTO]:
        self.expire_pending()
        return self.queue.list(state)

    def expire_pending(self) -> list[ApprovalDTO]:
        expired = self.queue.expire_pending()
        for approval in expired:
            self.audit.apply_approval_resolution(
                approval_id=approval.id,
                decision=Decision.deny,
                reason=f"Approval {approval.id} timed out.",
                execution_summary={"status": "not_executed", "approval_state": approval.state.value},
            )
        return expired

    def resolve(self, approval_id: str, action: str) -> ApprovalDTO:
        self.expire_pending()
        approval = self.queue.resolve(approval_id, action)
        final_args = approval.args
        execution_summary: dict[str, Any] | None = None

        if approval.state == ApprovalState.approved:
            execution_summary = DISPATCH[approval.tool](args=approval.args, gateway_token=self.settings.gateway_adapter_secret)
            self.audit.apply_approval_resolution(
                approval_id=approval.id,
                decision=Decision.allow,
                reason=f"Approval {approval.id} approved by human.",
                execution_summary=execution_summary,
            )
        elif approval.state == ApprovalState.redacted:
            final_args = redact_args(approval.args)
            execution_summary = DISPATCH[approval.tool](args=final_args, gateway_token=self.settings.gateway_adapter_secret)
            self.audit.apply_approval_resolution(
                approval_id=approval.id,
                decision=Decision.allow,
                reason=f"Approval {approval.id} approved with server-side redaction.",
                execution_summary=execution_summary,
                args=final_args,
                user_explanation="Sensitive arguments were redacted before execution.",
            )
            approval = approval.model_copy(update={"args": final_args})
        elif approval.state == ApprovalState.denied:
            self.audit.apply_approval_resolution(
                approval_id=approval.id,
                decision=Decision.deny,
                reason=f"Approval {approval.id} denied by human.",
                execution_summary={"status": "not_executed", "approval_state": approval.state.value},
            )

        return approval


def redact_args(args: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in args.items():
        if key in SENSITIVE_ARG_KEYS:
            redacted[key] = _redacted_value(value)
        elif isinstance(value, dict):
            redacted[key] = redact_args(value)
        else:
            redacted[key] = value
    return redacted


def _redacted_value(value: Any) -> Any:
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    if value is None:
        return None
    return "[REDACTED]"
