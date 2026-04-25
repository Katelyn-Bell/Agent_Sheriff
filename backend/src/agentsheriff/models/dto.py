from __future__ import annotations

from enum import StrEnum
from typing import Any, Annotated, Literal, Union

from pydantic import BaseModel, Field


class Decision(StrEnum):
    allow = "allow"
    deny = "deny"
    approval_required = "approval_required"


class ApprovalState(StrEnum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    redacted = "redacted"
    timed_out = "timed_out"


class PolicyStatus(StrEnum):
    draft = "draft"
    published = "published"
    archived = "archived"


class EvalStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RuleAction(StrEnum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"
    delegate_to_judge = "delegate_to_judge"


class ToolCallContext(BaseModel):
    task_id: str | None = None
    source_prompt: str | None = None
    source_content: str | None = None
    conversation_id: str | None = None

    model_config = {"extra": "allow"}


class ToolCallRequest(BaseModel):
    agent_id: str
    agent_label: str | None = None
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    context: ToolCallContext = Field(default_factory=ToolCallContext)


class ToolCallResponse(BaseModel):
    decision: Decision
    reason: str
    risk_score: int = Field(ge=0, le=100)
    matched_rule_id: str | None
    judge_used: bool
    policy_version_id: str
    audit_id: str
    approval_id: str | None = None
    user_explanation: str | None = None
    result: dict[str, Any] | None = None


class ToolMatchDTO(BaseModel):
    kind: Literal["exact", "namespace"]
    value: str


class ArgPredicateDTO(BaseModel):
    path: str
    operator: Literal["equals", "not_equals", "exists", "contains"]
    value: Any | None = None


class StaticRuleDTO(BaseModel):
    id: str
    name: str
    tool_match: ToolMatchDTO
    arg_predicates: list[ArgPredicateDTO] = Field(default_factory=list)
    action: RuleAction
    severity_floor: int | None = Field(default=None, ge=0, le=100)
    stop_on_match: bool = True
    reason: str
    user_explanation: str | None = None


class PolicyVersionDTO(BaseModel):
    id: str
    name: str
    version: int
    status: PolicyStatus
    intent_summary: str
    judge_prompt: str
    static_rules: list[StaticRuleDTO] = Field(default_factory=list)
    created_at: str
    published_at: str | None = None


class PolicyCreateRequest(BaseModel):
    name: str
    intent_summary: str = ""
    judge_prompt: str = ""
    static_rules: list[StaticRuleDTO] = Field(default_factory=list)


class PolicyUpdateRequest(BaseModel):
    name: str | None = None
    intent_summary: str | None = None
    judge_prompt: str | None = None
    static_rules: list[StaticRuleDTO] | None = None


class PolicyGenerationRequest(BaseModel):
    name: str
    user_intent: str
    tool_manifest: list[str] = Field(default_factory=list)


class PolicyGenerationResponse(BaseModel):
    intent_summary: str
    judge_prompt: str
    static_rules: list[StaticRuleDTO] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ApprovalDTO(BaseModel):
    id: str
    state: ApprovalState
    agent_id: str
    agent_label: str | None = None
    tool: str
    args: dict[str, Any]
    reason: str
    created_at: str
    expires_at: str
    policy_version_id: str


class ApprovalResolveRequest(BaseModel):
    action: Literal["approve", "deny", "redact"]


class AuditEntryDTO(BaseModel):
    id: str
    ts: str
    agent_id: str
    agent_label: str | None = None
    tool: str
    args: dict[str, Any]
    context: dict[str, Any]
    decision: Decision
    risk_score: int
    reason: str
    matched_rule_id: str | None
    judge_used: bool
    judge_rationale: str | None = None
    policy_version_id: str
    approval_id: str | None = None
    execution_summary: dict[str, Any] | None = None
    user_explanation: str | None = None


class EvalRunDTO(BaseModel):
    id: str
    policy_version_id: str
    status: EvalStatus
    created_at: str
    completed_at: str | None = None
    total_entries: int
    processed_entries: int
    agreed: int
    disagreed: int
    errored: int


class EvalResultDTO(BaseModel):
    id: str
    eval_run_id: str
    audit_id: str
    original_decision: Decision
    replayed_decision: Decision
    matched_rule_id: str | None
    judge_used: bool
    replay_reason: str
    agreement: bool


class AuditFrame(BaseModel):
    type: Literal["audit"] = "audit"
    payload: AuditEntryDTO


class ApprovalFrame(BaseModel):
    type: Literal["approval"] = "approval"
    payload: ApprovalDTO


class AgentStateFrame(BaseModel):
    type: Literal["agent_state"] = "agent_state"
    payload: dict[str, Any]


class PolicyPublishedFrame(BaseModel):
    type: Literal["policy_published"] = "policy_published"
    payload: PolicyVersionDTO


class EvalProgressFrame(BaseModel):
    type: Literal["eval_progress"] = "eval_progress"
    payload: EvalRunDTO


class HeartbeatFrame(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    ts: int


StreamFrame = Annotated[
    Union[AuditFrame, ApprovalFrame, AgentStateFrame, PolicyPublishedFrame, EvalProgressFrame, HeartbeatFrame],
    Field(discriminator="type"),
]
