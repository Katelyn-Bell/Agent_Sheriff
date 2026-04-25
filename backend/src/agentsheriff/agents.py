from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentsheriff.models.orm import Agent


class AgentStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_seen(self, agent_id: str, label: str | None) -> dict[str, str | None]:
        row = self.session.get(Agent, agent_id)
        if row is None:
            row = Agent(id=agent_id, label=label, state="active")
            self.session.add(row)
        elif label is not None:
            row.label = label
        self.session.commit()
        self.session.refresh(row)
        return self.to_dict(row)

    def list(self) -> list[dict[str, str | None]]:
        rows = self.session.scalars(select(Agent).order_by(Agent.updated_at.desc())).all()
        return [self.to_dict(row) for row in rows]

    def transition(self, agent_id: str, state: str) -> dict[str, str | None]:
        row = self.session.get(Agent, agent_id)
        if row is None:
            row = Agent(id=agent_id, label=None, state=state)
            self.session.add(row)
        else:
            row.state = state
        self.session.commit()
        self.session.refresh(row)
        return self.to_dict(row)

    @staticmethod
    def to_dict(row: Agent) -> dict[str, str | None]:
        return {"id": row.id, "label": row.label, "state": row.state}
