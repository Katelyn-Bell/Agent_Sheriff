from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.audit.store import AuditStore
from agentsheriff.models.dto import AuditEntryDTO, Decision

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("", response_model=list[AuditEntryDTO])
def list_audit(
    limit: int = 50,
    agent_id: str | None = None,
    decision: Decision | None = None,
    policy_version_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    session: Session = Depends(get_session),
) -> list[AuditEntryDTO]:
    return AuditStore(session).list_entries(
        limit=limit,
        agent_id=agent_id,
        decision=decision,
        policy_version_id=policy_version_id,
        since=since,
        until=until,
    )
