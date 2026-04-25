from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.audit.store import AuditStore
from agentsheriff.evals import EvalStore
from agentsheriff.models.dto import Decision, PolicyCreateRequest, RuleAction, StaticRuleDTO, ToolCallRequest, ToolMatchDTO
from agentsheriff.models.orm import Base
from agentsheriff.policy.store import PolicyStore


def test_eval_replays_audit_rows_against_policy_version() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as session:
        policy_store = PolicyStore(session)
        audit_store = AuditStore(session)
        policy = policy_store.create_draft(PolicyCreateRequest(
            name="Replay policy",
            static_rules=[StaticRuleDTO(
                id="deny_shell",
                name="Deny shell",
                tool_match=ToolMatchDTO(kind="namespace", value="shell"),
                action=RuleAction.deny,
                reason="Shell is blocked.",
            )],
        ))
        audit_store.record(
            request=ToolCallRequest(agent_id="a1", tool="shell.run", args={"cmd": "ls"}, context={}),
            decision=Decision.allow,
            risk_score=20,
            reason="Original allow",
            matched_rule_id=None,
            judge_used=True,
            judge_rationale="Original judge allowed",
            policy_version_id="pv_old",
            heuristic_summary={"risk_score": 20, "signals": []},
        )

        run = EvalStore(session).create_and_run(policy.id, {})
        results = EvalStore(session).list_results(run.id)

    assert run.status == "completed"
    assert run.total_entries == 1
    assert run.disagreed == 1
    assert results[0].original_decision == Decision.allow
    assert results[0].replayed_decision == Decision.deny
    assert results[0].agreement is False
