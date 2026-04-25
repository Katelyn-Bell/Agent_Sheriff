from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agentsheriff.models.dto import (
    PolicyGenerationResponse,
    SkillDTO,
    SkillLawGenerationRequest,
)
from agentsheriff.skills.laws import generate_skill_laws
from agentsheriff.skills.registry import get_parsed_skill, get_skill, installed_skills

router = APIRouter(prefix="/v1/skills", tags=["skills"])


@router.get("", response_model=list[SkillDTO])
def list_skills() -> list[SkillDTO]:
    return installed_skills()


@router.get("/{skill_id}", response_model=SkillDTO)
def read_skill(skill_id: str) -> SkillDTO:
    skill = get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' is not installed.")
    return skill


@router.post("/{skill_id}/generate-laws", response_model=PolicyGenerationResponse)
def generate_laws_for_skill(
    skill_id: str,
    request: SkillLawGenerationRequest,
) -> PolicyGenerationResponse:
    parsed = get_parsed_skill(skill_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' is not installed.")
    return generate_skill_laws(parsed, request.user_intent).to_response()
