from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from agentsheriff.agents import AgentStore
from agentsheriff.api.db import get_session
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.audit.store import AuditStore
from agentsheriff.gateway import handle_tool_call
from agentsheriff.models.dto import ToolCallRequest, ToolCallResponse
from agentsheriff.policy.store import PolicyStore

router = APIRouter(prefix="/v1", tags=["tool-calls"])


@router.post("/tool-call", response_model=ToolCallResponse)
async def tool_call(
    request: ToolCallRequest,
    app_request: Request,
    session: Session = Depends(get_session),
) -> ToolCallResponse:
    return await handle_tool_call(
        request,
        policy_store=PolicyStore(session),
        audit_store=AuditStore(session),
        settings=app_request.app.state.settings,
        approval_queue=ApprovalQueue(session),
        agent_store=AgentStore(session),
    )
