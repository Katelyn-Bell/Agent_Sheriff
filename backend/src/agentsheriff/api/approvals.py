from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.approvals.service import ApprovalService
from agentsheriff.models.dto import ApprovalDTO, ApprovalResolveRequest, ApprovalState
from agentsheriff.streams import hub

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalDTO])
def list_approvals(
    app_request: Request,
    state: ApprovalState | None = ApprovalState.pending,
    session: Session = Depends(get_session),
) -> list[ApprovalDTO]:
    return ApprovalService(session, app_request.app.state.settings).list(state)


@router.post("/{approval_id}", response_model=ApprovalDTO)
def resolve_approval(
    approval_id: str,
    request: ApprovalResolveRequest,
    app_request: Request,
    session: Session = Depends(get_session),
) -> ApprovalDTO:
    try:
        approval = ApprovalService(session, app_request.app.state.settings).resolve(approval_id, request.action)
        hub.broadcast_nowait({"type": "approval", "payload": approval.model_dump(mode="json")})
        return approval
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Approval not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
