from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from agentsheriff.config import Settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    intent_summary: Mapped[str] = mapped_column(Text, default="")
    judge_prompt: Mapped[str] = mapped_column(Text, default="")
    static_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    agent_id: Mapped[str] = mapped_column(String, index=True)
    agent_label: Mapped[str | None] = mapped_column(String, nullable=True)
    tool: Mapped[str] = mapped_column(String, index=True)
    args: Mapped[dict[str, Any]] = mapped_column(JSON)
    context: Mapped[dict[str, Any]] = mapped_column(JSON)
    heuristic_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    decision: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    matched_rule_id: Mapped[str | None] = mapped_column(String, nullable=True)
    judge_used: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_version_id: Mapped[str] = mapped_column(String, index=True)
    approval_id: Mapped[str | None] = mapped_column(String, nullable=True)
    execution_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    user_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    state: Mapped[str] = mapped_column(String, index=True)
    agent_id: Mapped[str] = mapped_column(String, index=True)
    agent_label: Mapped[str | None] = mapped_column(String, nullable=True)
    tool: Mapped[str] = mapped_column(String)
    args: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    policy_version_id: Mapped[str] = mapped_column(String, index=True)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    policy_version_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_entries: Mapped[int] = mapped_column(Integer, default=0)
    processed_entries: Mapped[int] = mapped_column(Integer, default=0)
    agreed: Mapped[int] = mapped_column(Integer, default=0)
    disagreed: Mapped[int] = mapped_column(Integer, default=0)
    errored: Mapped[int] = mapped_column(Integer, default=0)


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    eval_run_id: Mapped[str] = mapped_column(String, index=True)
    audit_id: Mapped[str] = mapped_column(String, index=True)
    original_decision: Mapped[str] = mapped_column(String)
    replayed_decision: Mapped[str] = mapped_column(String)
    matched_rule_id: Mapped[str | None] = mapped_column(String, nullable=True)
    judge_used: Mapped[bool] = mapped_column(Boolean, default=False)
    replay_reason: Mapped[str] = mapped_column(Text)
    agreement: Mapped[bool] = mapped_column(Boolean)


def build_engine(settings: Settings) -> Engine:
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, connect_args=connect_args)

    if settings.database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
