from __future__ import annotations

from fastapi import APIRouter

from agentsheriff.models.dto import Decision, ToolCallRequest, ToolCallResponse

router = APIRouter(prefix="/v1", tags=["tool-calls"])


@router.post("/tool-call", response_model=ToolCallResponse)
def tool_call(request: ToolCallRequest) -> ToolCallResponse:
    return ToolCallResponse(
        decision=Decision.allow,
        reason="Stub gateway allowed the call; policy engine wiring is next.",
        risk_score=10,
        matched_rule_id="stub.allow",
        judge_used=False,
        policy_version_id="pv_stub",
        audit_id="audit_stub",
        result={"status": "stubbed", "tool": request.tool},
    )
