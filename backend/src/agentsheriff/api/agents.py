from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentsheriff.agents import AgentStore
from agentsheriff.api.db import get_session

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("")
def list_agents(session: Session = Depends(get_session)) -> list[dict[str, str | None]]:
    return AgentStore(session).list()


@router.post("/{agent_id}/jail")
def jail_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    return AgentStore(session).transition(agent_id, "jailed")


@router.post("/{agent_id}/release")
def release_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    return AgentStore(session).transition(agent_id, "active")


@router.post("/{agent_id}/revoke")
def revoke_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    return AgentStore(session).transition(agent_id, "revoked")
