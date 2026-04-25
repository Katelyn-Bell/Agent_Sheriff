from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentsheriff.models.dto import (
    PolicyCreateRequest,
    PolicyStatus,
    RuleAction,
    SkillMatchDTO,
    StaticRuleDTO,
    ToolCallContext,
    ToolCallRequest,
    ToolMatchDTO,
)
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


def _kalshi_rule(skill_match: SkillMatchDTO | None) -> StaticRuleDTO:
    return StaticRuleDTO(
        id="deny_kalshi_trade",
        name="Deny Kalshi trade",
        tool_match=ToolMatchDTO(kind="exact", value="shell.run"),
        skill_match=skill_match,
        action=RuleAction.deny,
        reason="Kalshi trades blocked.",
    )


def test_skill_match_exact_fires_rule() -> None:
    request = ToolCallRequest(
        agent_id="a1",
        tool="shell.run",
        args={"command": "kalshi-cli orders create"},
        context=ToolCallContext(skill_id="kalshi-trading"),
    )
    rules = [_kalshi_rule(SkillMatchDTO(kind="exact", value="kalshi-trading"))]

    result = evaluate_static_rules(request, rules)

    assert result.action == RuleAction.deny
    assert result.matched_rule_id == "deny_kalshi_trade"


def test_skill_match_mismatch_skips_rule() -> None:
    request = ToolCallRequest(
        agent_id="a1",
        tool="shell.run",
        args={"command": "ls"},
        context=ToolCallContext(skill_id="other-skill"),
    )
    rules = [_kalshi_rule(SkillMatchDTO(kind="exact", value="kalshi-trading"))]

    result = evaluate_static_rules(request, rules)

    assert result.action == RuleAction.delegate_to_judge
    assert result.matched_rule_id is None


def test_skill_match_null_backwards_compatible() -> None:
    request = ToolCallRequest(
        agent_id="a1",
        tool="shell.run",
        args={"command": "ls"},
        context=ToolCallContext(),
    )
    rules = [_kalshi_rule(skill_match=None)]

    result = evaluate_static_rules(request, rules)

    assert result.action == RuleAction.deny
    assert result.matched_rule_id == "deny_kalshi_trade"


def test_skill_match_prefix_fires_for_versioned_skill() -> None:
    request = ToolCallRequest(
        agent_id="a1",
        tool="shell.run",
        args={"command": "kalshi-cli markets list"},
        context=ToolCallContext(skill_id="kalshi-trading-v2"),
    )
    rules = [_kalshi_rule(SkillMatchDTO(kind="prefix", value="kalshi"))]

    result = evaluate_static_rules(request, rules)

    assert result.action == RuleAction.deny
    assert result.matched_rule_id == "deny_kalshi_trade"


def test_skill_match_set_but_request_skill_id_missing_skips_rule() -> None:
    request = ToolCallRequest(
        agent_id="a1",
        tool="shell.run",
        args={"command": "kalshi-cli orders create"},
        context=ToolCallContext(),
    )
    rules = [_kalshi_rule(SkillMatchDTO(kind="exact", value="kalshi-trading"))]

    result = evaluate_static_rules(request, rules)

    assert result.action == RuleAction.delegate_to_judge
    assert result.matched_rule_id is None


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
