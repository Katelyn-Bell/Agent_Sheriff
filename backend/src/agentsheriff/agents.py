from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import AgentDTO
from agentsheriff.models.orm import Agent


class AgentStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_seen(self, agent_id: str, label: str | None) -> AgentDTO:
        row = self.session.get(Agent, agent_id)
        if row is None:
            row = Agent(id=agent_id, label=label, state="active")
            self.session.add(row)
        elif label is not None:
            row.label = label
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def list(self) -> list[AgentDTO]:
        rows = self.session.scalars(select(Agent).order_by(Agent.updated_at.desc())).all()
        return [self.to_dto(row) for row in rows]

    def transition(self, agent_id: str, state: str) -> AgentDTO:
        row = self.session.get(Agent, agent_id)
        if row is None:
            row = Agent(id=agent_id, label=None, state=state)
            self.session.add(row)
        else:
            row.state = state
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    @staticmethod
    def to_dto(row: Agent) -> AgentDTO:
        return AgentDTO(id=row.id, label=row.label, state=row.state)
