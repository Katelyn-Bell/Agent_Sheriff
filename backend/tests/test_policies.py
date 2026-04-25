from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.models.dto import PolicyCreateRequest, PolicyStatus, RuleAction, StaticRuleDTO, ToolCallRequest, ToolMatchDTO
from agentsheriff.models.orm import Base
from agentsheriff.policy.engine import evaluate_static_rules
from agentsheriff.policy.store import PolicyStore


def test_static_rule_first_match_and_severity_floor() -> None:
    request = ToolCallRequest(agent_id="a1", tool="github.push_branch", args={"force": True}, context={})
    rules = [
        StaticRuleDTO(
            id="allow_namespace",
            name="Allow GitHub",
            tool_match=ToolMatchDTO(kind="namespace", value="github"),
            action=RuleAction.allow,
            reason="Allow namespace",
        ),
        StaticRuleDTO(
            id="deny_force",
            name="Deny force",
            tool_match=ToolMatchDTO(kind="exact", value="github.push_branch"),
            action=RuleAction.deny,
            severity_floor=90,
            reason="Deny force",
        ),
    ]

    result = evaluate_static_rules(request, rules, base_risk_score=10)

    assert result.action == RuleAction.allow
    assert result.matched_rule_id == "allow_namespace"
    assert result.risk_score == 10


def test_static_rule_predicate_and_severity_floor() -> None:
    request = ToolCallRequest(agent_id="a1", tool="github.push_branch", args={"force": True}, context={})
    rules = [
        StaticRuleDTO(
            id="deny_force",
            name="Deny force",
            tool_match=ToolMatchDTO(kind="exact", value="github.push_branch"),
            arg_predicates=[{"path": "force", "operator": "equals", "value": True}],
            action=RuleAction.deny,
            severity_floor=90,
            reason="Deny force",
        ),
    ]

    result = evaluate_static_rules(request, rules, base_risk_score=10)

    assert result.action == RuleAction.deny
    assert result.matched_rule_id == "deny_force"
    assert result.risk_score == 90


def test_policy_store_create_and_publish() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as session:
        store = PolicyStore(session)
        draft = store.create_draft(PolicyCreateRequest(name="Finance assistant"))
        published = store.publish(draft.id)

    assert draft.status == PolicyStatus.draft
    assert published.status == PolicyStatus.published
    assert published.published_at is not None


def test_policy_store_archive_removes_version_from_active_lookup() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as session:
        store = PolicyStore(session)
        draft = store.create_draft(PolicyCreateRequest(name="Finance assistant"))
        published = store.publish(draft.id)
        archived = store.archive(published.id)
        active = store.active_published()

    assert archived.status == PolicyStatus.archived
    assert active is None
