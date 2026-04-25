from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from agentsheriff.agents import AgentStore
from agentsheriff.api.db import get_session
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.audit.store import AuditStore
from agentsheriff.gateway import handle_tool_call
from agentsheriff.openclaw import OpenClawCallEnvelope, OpenClawToolCallResult
from agentsheriff.openclaw.translator import translate_openclaw_call, translate_tool_call_response
from agentsheriff.policy.store import PolicyStore

router = APIRouter(prefix="/v1/openclaw", tags=["openclaw"])


@router.post("/tool-call", response_model=OpenClawToolCallResult)
async def openclaw_tool_call(
    envelope: OpenClawCallEnvelope,
    app_request: Request,
    session: Session = Depends(get_session),
) -> OpenClawToolCallResult:
    try:
        request = translate_openclaw_call(envelope)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = await handle_tool_call(
        request,
        policy_store=PolicyStore(session),
        audit_store=AuditStore(session),
        settings=app_request.app.state.settings,
        approval_queue=ApprovalQueue(session),
        agent_store=AgentStore(session),
        notifier=getattr(app_request.app.state, "notifier", None),
    )
    return translate_tool_call_response(response)
