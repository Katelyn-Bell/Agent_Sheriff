from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agentsheriff.models.dto import Decision, EvalResultDTO, EvalRunDTO, EvalStatus

router = APIRouter(prefix="/v1/evals", tags=["evals"])


class EvalCreateRequest(BaseModel):
    policy_version_id: str
    filters: dict[str, str] = Field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(run_id: str = "eval_stub", *, status: EvalStatus = EvalStatus.completed) -> EvalRunDTO:
    return EvalRunDTO(
        id=run_id,
        policy_version_id="pv_stub",
        status=status,
        created_at=_now(),
        completed_at=_now() if status == EvalStatus.completed else None,
        total_entries=1,
        processed_entries=1 if status == EvalStatus.completed else 0,
        agreed=1 if status == EvalStatus.completed else 0,
        disagreed=0,
        errored=0,
    )


@router.get("", response_model=list[EvalRunDTO])
def list_evals() -> list[EvalRunDTO]:
    return [_run()]


@router.post("", response_model=EvalRunDTO)
def create_eval(request: EvalCreateRequest) -> EvalRunDTO:
    _ = request.filters
    return _run("eval_created", status=EvalStatus.running).model_copy(update={"policy_version_id": request.policy_version_id})


@router.get("/{eval_id}", response_model=EvalRunDTO)
def get_eval(eval_id: str) -> EvalRunDTO:
    return _run(eval_id)


@router.get("/{eval_id}/results", response_model=list[EvalResultDTO])
def get_eval_results(eval_id: str) -> list[EvalResultDTO]:
    return [
        EvalResultDTO(
            id="er_stub",
            eval_run_id=eval_id,
            audit_id="audit_stub",
            original_decision=Decision.allow,
            replayed_decision=Decision.allow,
            matched_rule_id="stub.allow",
            judge_used=False,
            replay_reason="Stub replay matched the original decision.",
            agreement=True,
        )
    ]
