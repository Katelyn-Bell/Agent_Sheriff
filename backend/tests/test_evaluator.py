from __future__ import annotations

from agentsheriff.models.dto import Decision
from agentsheriff.threats.evaluator import DisagreementCategory
from agentsheriff.threats import compare_replayed_decision


def test_compare_replayed_decision_agreement() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.allow, "reason": "Allowed by read rule."},
        {"decision": Decision.allow, "reason": "Allowed by read rule."},
    )

    assert result.agreement is True
    assert result.disagreement_category is None


def test_compare_replayed_decision_more_permissive() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.deny, "reason": "Old policy denied."},
        {"decision": Decision.allow, "reason": "Draft now allows."},
    )

    assert result.agreement is False
    assert result.disagreement_category == DisagreementCategory.more_permissive


def test_compare_replayed_decision_more_restrictive() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.allow, "reason": "Old policy allowed."},
        {"decision": Decision.deny, "reason": "Draft now denies."},
    )

    assert result.agreement is False
    assert result.disagreement_category == DisagreementCategory.more_restrictive


def test_compare_replayed_decision_reason_changed() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.deny, "reason": "Blocked by static rule."},
        {"decision": Decision.deny, "reason": "Blocked by judge."},
    )

    assert result.agreement is False
    assert result.disagreement_category == DisagreementCategory.reason_changed


def test_compare_replayed_decision_approval_vs_direct() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.approval_required, "reason": "Needs review."},
        {"decision": Decision.allow, "reason": "Draft allows directly."},
    )

    assert result.agreement is False
    assert result.disagreement_category == DisagreementCategory.approval_vs_direct


def test_compare_replayed_decision_error() -> None:
    result = compare_replayed_decision(
        {"decision": Decision.allow, "reason": "Original allow."},
        {"error": True, "replay_reason": "Replay failed: bad rule."},
    )

    assert result.agreement is False
    assert result.replay_reason == "Replay failed: bad rule."
    assert result.disagreement_category == DisagreementCategory.error
