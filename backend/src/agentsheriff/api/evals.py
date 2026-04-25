from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.evals import EvalStore, run_eval_task
from agentsheriff.models.dto import EvalResultDTO, EvalRunDTO
from agentsheriff.streams import hub

router = APIRouter(prefix="/v1/evals", tags=["evals"])


class EvalCreateRequest(BaseModel):
    policy_version_id: str
    filters: dict[str, str] = Field(default_factory=dict)


@router.get("", response_model=list[EvalRunDTO])
def list_evals(session: Session = Depends(get_session)) -> list[EvalRunDTO]:
    return EvalStore(session).list_runs()


@router.post("", response_model=EvalRunDTO)
def create_eval(
    request: EvalCreateRequest,
    app_request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> EvalRunDTO:
    try:
        run = EvalStore(session).create_run(request.policy_version_id, request.filters)
        hub.broadcast_nowait({"type": "eval_progress", "payload": run.model_dump(mode="json")})
        background_tasks.add_task(
            _run_eval_background,
            app_request.app.state.session_factory,
            run.id,
            request.filters,
        )
        return run
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Policy version not found.") from exc


@router.get("/{eval_id}", response_model=EvalRunDTO)
def get_eval(eval_id: str, session: Session = Depends(get_session)) -> EvalRunDTO:
    run = EvalStore(session).get_run(eval_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Eval run not found.")
    return run


@router.get("/{eval_id}/results", response_model=list[EvalResultDTO])
def get_eval_results(eval_id: str, session: Session = Depends(get_session)) -> list[EvalResultDTO]:
    store = EvalStore(session)
    if store.get_run(eval_id) is None:
        raise HTTPException(status_code=404, detail="Eval run not found.")
    return store.list_results(eval_id)


async def _run_eval_background(session_factory, eval_id: str, filters: dict[str, str]) -> None:
    run_eval_task(
        session_factory,
        eval_id,
        filters,
        on_progress=lambda dto: hub.broadcast_nowait({"type": "eval_progress", "payload": dto.model_dump(mode="json")}),
    )
