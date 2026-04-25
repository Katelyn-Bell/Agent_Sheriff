from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentsheriff.agents import AgentStore
from agentsheriff.api.db import get_session
from agentsheriff.audit.store import AuditStore
from agentsheriff.models.dto import AgentDTO
from agentsheriff.streams import hub

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("", response_model=list[AgentDTO])
def list_agents(session: Session = Depends(get_session)) -> list[AgentDTO]:
    agents = AgentStore(session).list()
    if not agents:
        return agents
    counters = AuditStore(session).today_counters_for([a.id for a in agents])
    return [a.model_copy(update=counters.get(a.id, {})) for a in agents]


@router.post("/{agent_id}/jail", response_model=AgentDTO)
def jail_agent(agent_id: str, session: Session = Depends(get_session)) -> AgentDTO:
    agent = AgentStore(session).transition(agent_id, "jailed")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent.model_dump()})
    return agent


@router.post("/{agent_id}/release", response_model=AgentDTO)
def release_agent(agent_id: str, session: Session = Depends(get_session)) -> AgentDTO:
    agent = AgentStore(session).transition(agent_id, "active")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent.model_dump()})
    return agent


@router.post("/{agent_id}/revoke", response_model=AgentDTO)
def revoke_agent(agent_id: str, session: Session = Depends(get_session)) -> AgentDTO:
    agent = AgentStore(session).transition(agent_id, "revoked")
    hub.broadcast_nowait({"type": "agent_state", "payload": agent.model_dump()})
    return agent
