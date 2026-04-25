from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/agents", tags=["agents"])


def _agent(agent_id: str = "deputy-dusty", state: str = "active") -> dict[str, str]:
    return {"id": agent_id, "label": "Deputy Dusty", "state": state}


@router.get("")
def list_agents() -> list[dict[str, str]]:
    return [_agent()]


@router.post("/{agent_id}/jail")
def jail_agent(agent_id: str) -> dict[str, str]:
    return _agent(agent_id, "jailed")


@router.post("/{agent_id}/release")
def release_agent(agent_id: str) -> dict[str, str]:
    return _agent(agent_id, "active")


@router.post("/{agent_id}/revoke")
def revoke_agent(agent_id: str) -> dict[str, str]:
    return _agent(agent_id, "revoked")
