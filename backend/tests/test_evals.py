from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.audit.store import AuditStore
from agentsheriff.evals import EvalStore, run_eval_task
from agentsheriff.models.dto import Decision, PolicyCreateRequest, RuleAction, StaticRuleDTO, ToolCallRequest, ToolMatchDTO
from agentsheriff.models.orm import Base, PolicyVersion
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


def test_eval_progress_callback_runs_per_row_and_completion() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as session:
        policy_store = PolicyStore(session)
        audit_store = AuditStore(session)
        policy = policy_store.create_draft(PolicyCreateRequest(
            name="Replay policy",
            static_rules=[StaticRuleDTO(
                id="allow_gmail",
                name="Allow Gmail",
                tool_match=ToolMatchDTO(kind="namespace", value="gmail"),
                action=RuleAction.allow,
                reason="Gmail is allowed.",
            )],
        ))
        for idx in range(2):
            audit_store.record(
                request=ToolCallRequest(agent_id="a1", tool="gmail.read_inbox", args={"idx": idx}, context={}),
                decision=Decision.allow,
                risk_score=10,
                reason="Original allow",
                matched_rule_id=None,
                judge_used=False,
                judge_rationale=None,
                policy_version_id="pv_old",
                heuristic_summary={"risk_score": 10, "signals": []},
            )
        run = EvalStore(session).create_run(policy.id, {})
        progress: list[tuple[int, str]] = []

        completed = EvalStore(session).run_existing(
            run.id,
            {},
            on_progress=lambda dto: progress.append((dto.processed_entries, dto.status.value)),
        )

    assert completed.processed_entries == 2
    assert progress == [(1, "running"), (2, "running"), (2, "completed")]


def test_eval_background_task_marks_run_failed_on_setup_error() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as session:
        run = EvalStore(session).create_run(
            PolicyStore(session).create_draft(PolicyCreateRequest(name="broken later")).id,
            {},
        )
        policy_row = session.get(PolicyVersion, run.policy_version_id)
        assert policy_row is not None
        session.delete(policy_row)
        session.commit()

    progress: list[str] = []
    run_eval_task(Session, run.id, {}, on_progress=lambda dto: progress.append(dto.status.value))

    with Session() as session:
        failed = EvalStore(session).get_run(run.id)
        results = EvalStore(session).list_results(run.id)

    assert failed is not None
    assert failed.status == "failed"
    assert progress == ["failed"]
    assert results[0].audit_id == "eval_setup"
