from __future__ import annotations

from agentsheriff.demo.deputy_dusty import SCENARIOS, load_scenario
from agentsheriff.models.dto import Decision, PolicyStatus, PolicyVersionDTO, ToolCallRequest
from agentsheriff.threats import detect_threats, judge_tool_call


def _policy() -> PolicyVersionDTO:
    return PolicyVersionDTO(
        id="pv_demo",
        name="Demo fallback",
        version=1,
        status=PolicyStatus.published,
        intent_summary="Rules-only demo fallback policy.",
        judge_prompt="Use deterministic fallback for demo scenarios.",
        static_rules=[],
        created_at="2026-04-25T00:00:00Z",
        published_at="2026-04-25T00:00:00Z",
    )


def test_demo_scenarios_are_canonical_tool_call_requests() -> None:
    for scenario in SCENARIOS:
        payload = load_scenario(scenario)
        request = ToolCallRequest.model_validate(payload)
        assert request.agent_id == "deputy-dusty"
        assert request.tool


def test_demo_scenarios_preserve_rules_only_decision_buckets() -> None:
    expected = {
        "good": Decision.allow,
        "injection": Decision.deny,
        "approval": Decision.approval_required,
    }

    for scenario, decision in expected.items():
        request = ToolCallRequest.model_validate(load_scenario(scenario))
        result = judge_tool_call(_policy(), request, detect_threats(request))
        assert result.decision == decision
