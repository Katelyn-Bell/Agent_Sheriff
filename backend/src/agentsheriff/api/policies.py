from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from agentsheriff.models.dto import (
    PolicyCreateRequest,
    PolicyGenerationRequest,
    PolicyGenerationResponse,
    PolicyStatus,
    PolicyUpdateRequest,
    PolicyVersionDTO,
)

router = APIRouter(prefix="/v1/policies", tags=["policies"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stub_policy(policy_id: str = "pv_stub", *, status: PolicyStatus = PolicyStatus.draft) -> PolicyVersionDTO:
    published_at = _now() if status == PolicyStatus.published else None
    return PolicyVersionDTO(
        id=policy_id,
        name="Starter policy",
        version=1,
        status=status,
        intent_summary="Stub policy for frontend integration.",
        judge_prompt="Review delegated tool calls conservatively.",
        static_rules=[],
        created_at=_now(),
        published_at=published_at,
    )


@router.get("", response_model=list[PolicyVersionDTO])
def list_policies() -> list[PolicyVersionDTO]:
    return [_stub_policy()]


@router.post("", response_model=PolicyVersionDTO)
def create_policy(request: PolicyCreateRequest) -> PolicyVersionDTO:
    policy = _stub_policy("pv_draft")
    return policy.model_copy(update={
        "name": request.name,
        "intent_summary": request.intent_summary,
        "judge_prompt": request.judge_prompt,
        "static_rules": request.static_rules,
    })


@router.post("/generate", response_model=PolicyGenerationResponse)
def generate_policy(request: PolicyGenerationRequest) -> PolicyGenerationResponse:
    return PolicyGenerationResponse(
        intent_summary=f"Starter policy for {request.name}: {request.user_intent}",
        judge_prompt="Use the user's stated intent and prefer approval for irreversible actions.",
        static_rules=[],
        notes=["Stub generator response; Person 2 helper will replace this implementation."],
    )


@router.get("/{policy_id}", response_model=PolicyVersionDTO)
def get_policy(policy_id: str) -> PolicyVersionDTO:
    return _stub_policy(policy_id)


@router.put("/{policy_id}", response_model=PolicyVersionDTO)
def update_policy(policy_id: str, request: PolicyUpdateRequest) -> PolicyVersionDTO:
    policy = _stub_policy(policy_id)
    updates = request.model_dump(exclude_none=True)
    return policy.model_copy(update=updates)


@router.post("/{policy_id}/publish", response_model=PolicyVersionDTO)
def publish_policy(policy_id: str) -> PolicyVersionDTO:
    return _stub_policy(policy_id, status=PolicyStatus.published)
