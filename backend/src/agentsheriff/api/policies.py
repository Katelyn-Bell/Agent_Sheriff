from __future__ import annotations

import importlib.resources
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.models.dto import (
    ArgPredicateDTO,
    PolicyCreateRequest,
    PolicyGenerationRequest,
    PolicyGenerationResponse,
    PolicyUpdateRequest,
    PolicyVersionDTO,
    RuleAction,
    StaticRuleDTO,
    ToolMatchDTO,
)
from agentsheriff.policy.store import PolicyStore
from agentsheriff.streams import hub
from agentsheriff.threats import generate_starter_policy

router = APIRouter(prefix="/v1/policies", tags=["policies"])

_TEMPLATES_DIR = Path(__file__).parent.parent / "policy" / "templates"
_TEMPLATE_NAMES = ("default", "healthcare", "finance", "startup")


@router.get("", response_model=list[PolicyVersionDTO])
def list_policies(session: Session = Depends(get_session)) -> list[PolicyVersionDTO]:
    return PolicyStore(session).list_versions()


@router.post("", response_model=PolicyVersionDTO)
def create_policy(request: PolicyCreateRequest, session: Session = Depends(get_session)) -> PolicyVersionDTO:
    return PolicyStore(session).create_draft(request)


@router.post("/generate", response_model=PolicyGenerationResponse)
def generate_policy(request: PolicyGenerationRequest) -> PolicyGenerationResponse:
    _ = request.name
    return generate_starter_policy(request.user_intent, request.tool_manifest).to_response()


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
        policy = PolicyStore(session).publish(policy_id)
        hub.broadcast_nowait({"type": "policy_published", "payload": policy.model_dump(mode="json")})
        return policy
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Policy version not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{policy_id}/archive", response_model=PolicyVersionDTO)
def archive_policy(policy_id: str, session: Session = Depends(get_session)) -> PolicyVersionDTO:
    try:
        return PolicyStore(session).archive(policy_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Policy version not found.") from exc


@router.get("/templates", response_model=list[str])
def list_templates() -> list[str]:
    return list(_TEMPLATE_NAMES)


@router.post("/apply-template", response_model=PolicyVersionDTO)
def apply_template(
    body: dict,
    session: Session = Depends(get_session),
) -> PolicyVersionDTO:
    name = body.get("name", "")
    if name not in _TEMPLATE_NAMES:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found. Available: {list(_TEMPLATE_NAMES)}")
    template_path = _TEMPLATES_DIR / f"{name}.yaml"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail=f"Template file for '{name}' not found on disk.")
    raw = yaml.safe_load(template_path.read_text())
    rules = [_parse_rule(r) for r in raw.get("rules", [])]
    create_req = PolicyCreateRequest(
        name=raw.get("name", name.title()),
        intent_summary=raw.get("intent_summary", ""),
        judge_prompt=raw.get("judge_prompt", ""),
        static_rules=rules,
    )
    policy = PolicyStore(session).create_draft(create_req)
    hub.broadcast_nowait({"type": "policy_published", "payload": policy.model_dump(mode="json")})
    return policy


def _parse_rule(raw: dict) -> StaticRuleDTO:
    tool_match_raw = raw["tool_match"]
    tool_match = ToolMatchDTO(kind=tool_match_raw["kind"], value=tool_match_raw["value"])
    predicates = [
        ArgPredicateDTO(path=p["path"], operator=p["operator"], value=p.get("value"))
        for p in raw.get("arg_predicates", [])
    ]
    return StaticRuleDTO(
        id=raw["id"],
        name=raw.get("name", raw["id"]),
        tool_match=tool_match,
        arg_predicates=predicates,
        action=RuleAction(raw["action"]),
        severity_floor=raw.get("severity_floor"),
        jail_on_deny=raw.get("jail_on_deny", False),
        stop_on_match=raw.get("stop_on_match", True),
        reason=raw.get("reason", ""),
        user_explanation=raw.get("user_explanation"),
    )
