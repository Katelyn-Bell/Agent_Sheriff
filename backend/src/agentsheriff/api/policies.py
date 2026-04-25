from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.models.dto import (
    PolicyCreateRequest,
    PolicyGenerationRequest,
    PolicyGenerationResponse,
    PolicyUpdateRequest,
    PolicyVersionDTO,
)
from agentsheriff.policy.store import PolicyStore

router = APIRouter(prefix="/v1/policies", tags=["policies"])


@router.get("", response_model=list[PolicyVersionDTO])
def list_policies(session: Session = Depends(get_session)) -> list[PolicyVersionDTO]:
    return PolicyStore(session).list_versions()


@router.post("", response_model=PolicyVersionDTO)
def create_policy(request: PolicyCreateRequest, session: Session = Depends(get_session)) -> PolicyVersionDTO:
    return PolicyStore(session).create_draft(request)


@router.post("/generate", response_model=PolicyGenerationResponse)
def generate_policy(request: PolicyGenerationRequest) -> PolicyGenerationResponse:
    return PolicyGenerationResponse(
        intent_summary=f"Starter policy for {request.name}: {request.user_intent}",
        judge_prompt="Use the user's stated intent and prefer approval for irreversible actions.",
        static_rules=[],
        notes=["Stub generator response; Person 2 helper will replace this implementation."],
    )


@router.get("/{policy_id}", response_model=PolicyVersionDTO)
def get_policy(policy_id: str, session: Session = Depends(get_session)) -> PolicyVersionDTO:
    policy = PolicyStore(session).get_version(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy version not found.")
    return policy


@router.put("/{policy_id}", response_model=PolicyVersionDTO)
def update_policy(
    policy_id: str,
    request: PolicyUpdateRequest,
    session: Session = Depends(get_session),
) -> PolicyVersionDTO:
    try:
        return PolicyStore(session).update_draft(policy_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Policy version not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{policy_id}/publish", response_model=PolicyVersionDTO)
def publish_policy(policy_id: str, session: Session = Depends(get_session)) -> PolicyVersionDTO:
    try:
        return PolicyStore(session).publish(policy_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Policy version not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
