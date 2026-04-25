from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.audit.store import AuditStore
from agentsheriff.models.dto import Decision, ToolCallRequest
from agentsheriff.models.orm import AuditEntry, Base


def test_audit_filters_by_agent_decision_policy_and_time_window() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        store = AuditStore(session)
        old = store.record(
            request=ToolCallRequest(agent_id="a1", tool="gmail.read_inbox", args={}, context={}),
            decision=Decision.allow,
            risk_score=10,
            reason="old",
            matched_rule_id="old_rule",
            judge_used=False,
            judge_rationale=None,
            policy_version_id="pv_old",
            heuristic_summary={"risk_score": 10, "signals": []},
        )
        hit = store.record(
            request=ToolCallRequest(agent_id="a2", tool="shell.run", args={"cmd": "ls"}, context={}),
            decision=Decision.deny,
            risk_score=90,
            reason="hit",
            matched_rule_id="hit_rule",
            judge_used=False,
            judge_rationale=None,
            policy_version_id="pv_hit",
            heuristic_summary={"risk_score": 90, "signals": ["shell"]},
        )
        old_row = session.get(AuditEntry, old.id)
        assert old_row is not None
        old_row.ts = now - timedelta(days=3)
        hit_row = session.get(AuditEntry, hit.id)
        assert hit_row is not None
        hit_row.ts = now
        session.commit()

        rows = store.list_entries(
            agent_id="a2",
            decision=Decision.deny,
            policy_version_id="pv_hit",
            since=(now - timedelta(minutes=1)).isoformat(),
            until=(now + timedelta(minutes=1)).isoformat(),
        )

    assert [row.id for row in rows] == [hit.id]
    assert rows[0].heuristic_summary == {"risk_score": 90, "signals": ["shell"]}
