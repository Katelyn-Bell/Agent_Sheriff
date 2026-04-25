// Mirrors backend DTOs frozen in specs/integration-and-handoffs.md.
// Field names are wire-format; do not rename without a spec update.

export type Decision = "allow" | "deny" | "approval_required";

export type ApprovalState =
  | "pending"
  | "approved"
  | "denied"
  | "redacted"
  | "timed_out";

export type PolicyStatus = "draft" | "published" | "archived";

export type RuleAction =
  | "allow"
  | "deny"
  | "require_approval"
  | "delegate_to_judge";

export type ToolMatchKind = "exact" | "namespace";
export type SkillMatchKind = "exact" | "prefix";

export type DisagreementCategory =
  | "more_permissive"
  | "more_restrictive"
  | "reason_changed"
  | "approval_vs_direct"
  | "error";

export interface ToolCallContext {
  task_id?: string | null;
  source_prompt?: string | null;
  source_content?: string | null;
  conversation_id?: string | null;
  skill_id?: string | null;
  [key: string]: unknown;
}

export interface ToolCallRequest {
  agent_id: string;
  agent_label?: string;
  tool: string;
  args: Record<string, unknown>;
  context: ToolCallContext;
}

export interface ExecutionResult {
  status: string;
  [key: string]: unknown;
}

export interface ToolCallResponse {
  decision: Decision;
  reason: string;
  risk_score: number;
  matched_rule_id: string | null;
  judge_used: boolean;
  policy_version_id: string;
  audit_id: string;
  approval_id: string | null;
  user_explanation: string | null;
  result?: ExecutionResult;
}

export interface ArgPredicate {
  path: string;
  operator: string;
  value: unknown;
}

export interface ToolMatch {
  kind: ToolMatchKind;
  value: string;
}

export interface SkillMatch {
  kind: SkillMatchKind;
  value: string;
}

export interface StaticRuleDTO {
  id: string;
  name: string;
  tool_match: ToolMatch;
  skill_match?: SkillMatch | null;
  arg_predicates: ArgPredicate[];
  action: RuleAction;
  severity_floor?: number;
  stop_on_match?: boolean;
  reason?: string;
  user_explanation?: string;
}

export interface PolicyVersionDTO {
  id: string;
  name: string;
  version: number;
  status: PolicyStatus;
  intent_summary: string;
  judge_prompt: string;
  static_rules: StaticRuleDTO[];
  created_at: string;
  published_at: string | null;
}

export interface PolicyGenerationRequest {
  name: string;
  user_intent: string;
  tool_manifest: string[];
  domain_hint?: string;
}

export interface PolicyGenerationResponse {
  intent_summary: string;
  judge_prompt: string;
  static_rules: StaticRuleDTO[];
  notes: string[];
}

export interface ToolDefinitionDTO {
  id: string;
  namespace: string;
  label: string;
  risk_hints: string[];
  args_schema_summary: Record<string, string>;
  replay_safe: boolean;
}

export interface SkillCommandDTO {
  name: string;
  flags: string[];
  risky_flags: string[];
  description?: string | null;
  example?: string | null;
}

export interface SkillDTO {
  id: string;
  name: string;
  description?: string | null;
  base_command: string;
  commands: SkillCommandDTO[];
  risky_flags: string[];
}

export interface SkillLawGenerationRequest {
  user_intent: string;
  guardrails?: string | null;
}

export type RuleOverrideAction = "allow" | "require_approval" | "deny";

export type RuleOverrides = Record<string, RuleOverrideAction>;

export interface EvalRunDTO {
  id: string;
  policy_version_id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  total_entries: number;
  processed_entries: number;
  agreed: number;
  disagreed: number;
  errored: number;
}

export interface EvalResultDTO {
  id: string;
  eval_run_id: string;
  audit_id: string;
  original_decision: Decision;
  replayed_decision: Decision;
  matched_rule_id: string | null;
  judge_used: boolean;
  replay_reason: string;
  agreement: boolean;
  disagreement_category?: DisagreementCategory;
}

export interface ApprovalDTO {
  id: string;
  state: ApprovalState;
  agent_id: string;
  agent_label?: string;
  tool: string;
  args: Record<string, unknown>;
  reason: string;
  user_explanation: string | null;
  created_at: string;
  expires_at: string;
  policy_version_id: string;
}

export type ApprovalResolution = "approve" | "deny" | "redact";

// Inferred from specs/_shared-context.md §"Audit and eval expectations" and
// specs/person-3-dashboard-ui.md §"Rich audit detail". Reconcile with Person 1
// when backend ORM/DTO lands.
export interface AuditEntryDTO {
  id: string;
  ts: string;
  agent_id: string;
  agent_label?: string;
  tool: string;
  args: Record<string, unknown>;
  context: ToolCallContext;
  heuristic_summary: Record<string, unknown>;
  risk_score: number;
  matched_rule_id: string | null;
  judge_used: boolean;
  judge_rationale: string | null;
  decision: Decision;
  reason: string;
  user_explanation: string | null;
  approval_id: string | null;
  execution_summary: Record<string, unknown> | null;
  policy_version_id: string;
}

export type AgentState = "active" | "jailed" | "revoked" | "idle";

export interface AgentStateDTO {
  agent_id: string;
  agent_label?: string;
  state: AgentState;
  request_count: number;
  blocked_count: number;
  active_policy_version_id: string | null;
  last_decision: Decision | null;
  last_seen_at: string | null;
}

export interface HealthResponse {
  status: "ok" | string;
}

export interface UserDTO {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  onboarded: boolean;
  created_at: string;
}

export interface AuditQuery {
  limit?: number;
  agent_id?: string;
  decision?: Decision;
  policy_version_id?: string;
  since?: string;
}

export type StreamFrame =
  | { type: "audit"; payload: AuditEntryDTO }
  | { type: "approval"; payload: ApprovalDTO }
  | { type: "agent_state"; payload: AgentStateDTO }
  | { type: "policy_published"; payload: PolicyVersionDTO }
  | { type: "eval_progress"; payload: EvalRunDTO }
  | { type: "heartbeat"; ts: number };

export type StreamFrameType = StreamFrame["type"];
