import type { AgentState, AgentStateDTO } from "./types";

export type RawAgentStateDTO = Partial<AgentStateDTO> & {
  id?: string;
  label?: string | null;
  requests_today?: number;
  blocked_today?: number;
};

const AGENT_STATES = new Set<AgentState>(["active", "idle", "jailed", "revoked"]);

export function normalizeAgentState(raw: RawAgentStateDTO): AgentStateDTO {
  const state = AGENT_STATES.has(raw.state as AgentState)
    ? (raw.state as AgentState)
    : "idle";

  return {
    agent_id: raw.agent_id ?? raw.id ?? "",
    agent_label: raw.agent_label ?? raw.label ?? undefined,
    state,
    request_count: raw.request_count ?? raw.requests_today ?? 0,
    blocked_count: raw.blocked_count ?? raw.blocked_today ?? 0,
    active_policy_version_id: raw.active_policy_version_id ?? null,
    last_decision: raw.last_decision ?? null,
    last_seen_at: raw.last_seen_at ?? null,
  };
}

export function mergeAgentState(
  previous: AgentStateDTO | undefined,
  raw: RawAgentStateDTO,
): AgentStateDTO {
  const next = normalizeAgentState(raw);
  return {
    ...previous,
    ...next,
    agent_label: next.agent_label ?? previous?.agent_label,
    request_count:
      raw.request_count ?? raw.requests_today ?? previous?.request_count ?? 0,
    blocked_count:
      raw.blocked_count ?? raw.blocked_today ?? previous?.blocked_count ?? 0,
    active_policy_version_id:
      next.active_policy_version_id ?? previous?.active_policy_version_id ?? null,
    last_decision: next.last_decision ?? previous?.last_decision ?? null,
    last_seen_at: next.last_seen_at ?? previous?.last_seen_at ?? null,
  };
}
