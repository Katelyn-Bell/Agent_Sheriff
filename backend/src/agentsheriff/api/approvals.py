from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from agentsheriff.models.dto import ApprovalDTO, ApprovalResolveRequest, ApprovalState

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


def _approval(state: ApprovalState = ApprovalState.pending) -> ApprovalDTO:
    now = datetime.now(timezone.utc)
    return ApprovalDTO(
        id="approval_stub",
        state=state,
        agent_id="deputy-dusty",
        agent_label="Deputy Dusty",
        tool="gmail.send_email",
        args={"to": "accountant@example.com"},
        reason="Stub approval for frontend integration.",
        created_at=now.isoformat().replace("+00:00", "Z"),
        expires_at=(now + timedelta(minutes=2)).isoformat().replace("+00:00", "Z"),
        policy_version_id="pv_stub",
    )


@router.get("", response_model=list[ApprovalDTO])
def list_approvals(state: ApprovalState | None = ApprovalState.pending) -> list[ApprovalDTO]:
    approval = _approval()
    if state is not None and approval.state != state:
        return []
    return [approval]


@router.post("/{approval_id}", response_model=ApprovalDTO)
def resolve_approval(approval_id: str, request: ApprovalResolveRequest) -> ApprovalDTO:
    state = {
        "approve": ApprovalState.approved,
        "deny": ApprovalState.denied,
        "redact": ApprovalState.redacted,
    }[request.action]
    return _approval(state).model_copy(update={"id": approval_id})
