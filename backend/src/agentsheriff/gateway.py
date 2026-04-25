from __future__ import annotations

from agentsheriff.adapters.manifest import DISPATCH, supported_tools
from agentsheriff.agents import AgentStore
from agentsheriff.approvals.queue import ApprovalQueue
from agentsheriff.audit.store import AuditStore
from agentsheriff.config import Settings
from agentsheriff.models.dto import Decision, PolicyStatus, PolicyVersionDTO, RuleAction, ToolCallRequest, ToolCallResponse
from agentsheriff.policy.engine import evaluate_static_rules
from agentsheriff.policy.store import PolicyStore
from agentsheriff.threats.detector import detect_threats, judge_tool_call


def handle_tool_call(
    request: ToolCallRequest,
    *,
    policy_store: PolicyStore,
    audit_store: AuditStore,
    settings: Settings,
    approval_queue: ApprovalQueue | None = None,
    agent_store: AgentStore | None = None,
) -> ToolCallResponse:
    if agent_store is not None:
        agent_store.upsert_seen(request.agent_id, request.agent_label)

    if request.tool not in supported_tools():
        audit = audit_store.record(
            request=request,
            decision=Decision.deny,
            risk_score=100,
            reason=f"Unknown tool '{request.tool}'.",
            matched_rule_id=None,
            judge_used=False,
            judge_rationale=None,
            policy_version_id="pv_unvalidated",
            heuristic_summary={},
            execution_summary=None,
            user_explanation="This tool is not in the adapter manifest.",
        )
        return _response_from_audit(audit)

    threat_report = detect_threats(request)
    policy = policy_store.active_published() or _implicit_policy()
    evaluation = evaluate_static_rules(request, policy.static_rules, base_risk_score=threat_report.risk_score)

    judge_used = False
    judge_rationale = None
    user_explanation = evaluation.user_explanation
    decision = _decision_from_rule_action(evaluation.action)
    risk_score = evaluation.risk_score
    reason = evaluation.reason

    if evaluation.action == RuleAction.delegate_to_judge:
        judge = judge_tool_call(policy, request, threat_report)
        judge_used = True
        judge_rationale = judge.rationale
        decision = judge.decision
        risk_score = judge.risk_score
        reason = judge.rationale
        user_explanation = judge.user_explanation

    execution_summary = None
    approval_id = None
    if decision == Decision.allow:
        execution_summary = DISPATCH[request.tool](args=request.args, gateway_token=settings.gateway_adapter_secret)
    elif decision == Decision.approval_required and approval_queue is not None:
        approval = approval_queue.create_pending(
            request=request,
            reason=reason,
            policy_version_id=policy.id,
            timeout_s=settings.approval_timeout_s,
        )
        approval_id = approval.id

    audit = audit_store.record(
        request=request,
        decision=decision,
        risk_score=risk_score,
        reason=reason,
        matched_rule_id=evaluation.matched_rule_id,
        judge_used=judge_used,
        judge_rationale=judge_rationale,
        policy_version_id=policy.id,
        heuristic_summary=threat_report.summary(),
        approval_id=approval_id,
        execution_summary=execution_summary,
        user_explanation=user_explanation,
    )
    return _response_from_audit(audit)


def _decision_from_rule_action(action: RuleAction) -> Decision:
    if action == RuleAction.allow:
        return Decision.allow
    if action == RuleAction.deny:
        return Decision.deny
    if action == RuleAction.require_approval:
        return Decision.approval_required
    return Decision.deny


def _implicit_policy() -> PolicyVersionDTO:
    return PolicyVersionDTO(
        id="pv_unpublished",
        name="Implicit unpublished policy",
        version=0,
        status=PolicyStatus.published,
        intent_summary="No active policy has been published yet.",
        judge_prompt="Use conservative defaults until a policy is published.",
        static_rules=[],
        created_at="1970-01-01T00:00:00Z",
        published_at="1970-01-01T00:00:00Z",
    )


def _response_from_audit(audit) -> ToolCallResponse:
    return ToolCallResponse(
        decision=audit.decision,
        reason=audit.reason,
        risk_score=audit.risk_score,
        matched_rule_id=audit.matched_rule_id,
        judge_used=audit.judge_used,
        policy_version_id=audit.policy_version_id,
        audit_id=audit.id,
        approval_id=audit.approval_id,
        user_explanation=audit.user_explanation,
        result=audit.execution_summary if audit.decision == Decision.allow else None,
    )
