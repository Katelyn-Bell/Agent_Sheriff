from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentsheriff.models.dto import PolicyCreateRequest, PolicyStatus, PolicyUpdateRequest, PolicyVersionDTO, StaticRuleDTO
from agentsheriff.models.orm import PolicyVersion


def utc_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class PolicyStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_versions(self) -> list[PolicyVersionDTO]:
        rows = self.session.scalars(select(PolicyVersion).order_by(PolicyVersion.created_at.desc())).all()
        return [self.to_dto(row) for row in rows]

    def create_draft(self, request: PolicyCreateRequest) -> PolicyVersionDTO:
        next_version = (self.session.scalar(select(func.max(PolicyVersion.version))) or 0) + 1
        row = PolicyVersion(
            id=f"pv_{uuid4().hex[:12]}",
            name=request.name,
            version=next_version,
            status=PolicyStatus.draft.value,
            intent_summary=request.intent_summary,
            judge_prompt=request.judge_prompt,
            static_rules=[rule.model_dump(mode="json") for rule in request.static_rules],
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def get_version(self, policy_id: str) -> PolicyVersionDTO | None:
        row = self.session.get(PolicyVersion, policy_id)
        return self.to_dto(row) if row else None

    def require_row(self, policy_id: str) -> PolicyVersion:
        row = self.session.get(PolicyVersion, policy_id)
        if row is None:
            raise KeyError(policy_id)
        return row

    def update_draft(self, policy_id: str, request: PolicyUpdateRequest) -> PolicyVersionDTO:
        row = self.require_row(policy_id)
        if row.status != PolicyStatus.draft.value:
            raise ValueError("Only draft policies can be updated.")
        updates = request.model_dump(exclude_none=True, exclude={"static_rules"})
        for field, value in updates.items():
            setattr(row, field, value)
        if request.static_rules is not None:
            row.static_rules = [rule.model_dump(mode="json") for rule in request.static_rules]
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def publish(self, policy_id: str) -> PolicyVersionDTO:
        row = self.require_row(policy_id)
        if row.status == PolicyStatus.archived.value:
            raise ValueError("Archived policies cannot be published.")
        row.status = PolicyStatus.published.value
        row.published_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def archive(self, policy_id: str) -> PolicyVersionDTO:
        row = self.require_row(policy_id)
        row.status = PolicyStatus.archived.value
        row.archived_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(row)
        return self.to_dto(row)

    def active_published(self) -> PolicyVersionDTO | None:
        statement = (
            select(PolicyVersion)
            .where(PolicyVersion.status == PolicyStatus.published.value)
            .order_by(PolicyVersion.published_at.desc(), PolicyVersion.version.desc())
            .limit(1)
        )
        row = self.session.scalar(statement)
        return self.to_dto(row) if row else None

    @staticmethod
    def to_dto(row: PolicyVersion) -> PolicyVersionDTO:
        return PolicyVersionDTO(
            id=row.id,
            name=row.name,
            version=row.version,
            status=PolicyStatus(row.status),
            intent_summary=row.intent_summary,
            judge_prompt=row.judge_prompt,
            static_rules=[StaticRuleDTO.model_validate(rule) for rule in row.static_rules],
            created_at=utc_iso(row.created_at) or "",
            published_at=utc_iso(row.published_at),
        )
