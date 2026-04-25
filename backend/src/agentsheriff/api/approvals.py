from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.models.dto import ApprovalDTO, ApprovalResolveRequest, ApprovalState
from agentsheriff.streams import hub

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalDTO])
def list_approvals(
    state: ApprovalState | None = ApprovalState.pending,
    session: Session = Depends(get_session),
) -> list[ApprovalDTO]:
    return ApprovalQueue(session).list(state)


@router.post("/{approval_id}", response_model=ApprovalDTO)
def resolve_approval(
    approval_id: str,
    request: ApprovalResolveRequest,
    session: Session = Depends(get_session),
) -> ApprovalDTO:
    try:
        approval = ApprovalQueue(session).resolve(approval_id, request.action)
        hub.broadcast_nowait({"type": "approval", "payload": approval.model_dump(mode="json")})
        return approval
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Approval not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
