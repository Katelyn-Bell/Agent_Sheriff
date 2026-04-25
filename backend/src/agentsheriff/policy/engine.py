from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentsheriff.models.dto import RuleAction, StaticRuleDTO, ToolCallRequest


@dataclass(frozen=True)
class PolicyEvaluation:
    action: RuleAction
    risk_score: int
    matched_rule_id: str | None
    reason: str
    user_explanation: str | None


def evaluate_static_rules(
    request: ToolCallRequest,
    rules: list[StaticRuleDTO],
    *,
    base_risk_score: int = 0,
) -> PolicyEvaluation:
    for rule in rules:
        if _tool_matches(request.tool, rule) and _predicates_match(request.args, rule):
            risk_score = max(base_risk_score, rule.severity_floor or 0)
            return PolicyEvaluation(
                action=rule.action,
                risk_score=risk_score,
                matched_rule_id=rule.id,
                reason=rule.reason,
                user_explanation=rule.user_explanation,
            )

    return PolicyEvaluation(
        action=RuleAction.delegate_to_judge,
        risk_score=base_risk_score,
        matched_rule_id=None,
        reason="No static rule matched; delegated to judge.",
        user_explanation=None,
    )


def _tool_matches(tool: str, rule: StaticRuleDTO) -> bool:
    if rule.tool_match.kind == "exact":
        return tool == rule.tool_match.value
    if rule.tool_match.kind == "namespace":
        namespace = rule.tool_match.value.rstrip(".")
        return tool == namespace or tool.startswith(f"{namespace}.")
    return False


def _predicates_match(args: dict[str, Any], rule: StaticRuleDTO) -> bool:
    return all(_predicate_matches(args, predicate.path, predicate.operator, predicate.value) for predicate in rule.arg_predicates)


def _predicate_matches(args: dict[str, Any], path: str, operator: str, expected: Any) -> bool:
    exists, actual = _get_path(args, path)
    if operator == "exists":
        return exists if expected is None else exists == bool(expected)
    if not exists:
        return False
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        if isinstance(actual, str):
            return str(expected) in actual
        if isinstance(actual, list):
            return expected in actual
        return False
    return False


def _get_path(args: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = args
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current
