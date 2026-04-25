from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentsheriff.agents import AgentStore
from agentsheriff.api.db import get_session
from agentsheriff.streams import hub

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("")
def list_agents(session: Session = Depends(get_session)) -> list[dict[str, str | None]]:
    return AgentStore(session).list()


@router.post("/{agent_id}/jail")
def jail_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    agent = AgentStore(session).transition(agent_id, "jailed")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent})
    return agent


@router.post("/{agent_id}/release")
def release_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    agent = AgentStore(session).transition(agent_id, "active")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent})
    return agent


@router.post("/{agent_id}/revoke")
def revoke_agent(agent_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:
    agent = AgentStore(session).transition(agent_id, "revoked")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent})
    return agent
