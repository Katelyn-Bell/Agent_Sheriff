import { create } from "zustand";
import type {
  AgentStateDTO,
  ApprovalDTO,
  AuditEntryDTO,
  EvalRunDTO,
  PolicyVersionDTO,
  StaticRuleDTO,
  StreamFrame,
} from "./types";

export interface DraftPolicy {
  name: string;
  intent_summary: string;
  judge_prompt: string;
  static_rules: StaticRuleDTO[];
  notes: string[];
  source: "generated" | "manual";
}

const AUDIT_CAP = 200;

export type ConnectionState = "connecting" | "connected" | "disconnected";

interface StoreState {
  audit: AuditEntryDTO[];
  approvals: Record<string, ApprovalDTO>;
  agents: Record<string, AgentStateDTO>;
  evals: Record<string, EvalRunDTO>;
  latestPolicy: PolicyVersionDTO | null;
  draftPolicy: DraftPolicy | null;
  connection: ConnectionState;
  lastHeartbeatTs: number | null;

  applyFrame: (frame: StreamFrame) => void;
  rehydrate: (snapshot: Partial<Snapshot>) => void;
  setConnection: (c: ConnectionState) => void;
  setDraftPolicy: (draft: DraftPolicy | null) => void;
  updateDraftPolicy: (patch: Partial<DraftPolicy>) => void;
}

export interface Snapshot {
  audit: AuditEntryDTO[];
  approvals: ApprovalDTO[];
  agents: AgentStateDTO[];
  evals: EvalRunDTO[];
  latestPolicy: PolicyVersionDTO | null;
}

export const useAppStore = create<StoreState>((set) => ({
  audit: [],
  approvals: {},
  agents: {},
  evals: {},
  latestPolicy: null,
  draftPolicy: null,
  connection: "connecting",
  lastHeartbeatTs: null,

  applyFrame: (frame) =>
    set((s) => {
      switch (frame.type) {
        case "audit":
          return {
            audit: [frame.payload, ...s.audit].slice(0, AUDIT_CAP),
          };
        case "approval":
          return {
            approvals: { ...s.approvals, [frame.payload.id]: frame.payload },
          };
        case "agent_state":
          return {
            agents: {
              ...s.agents,
              [frame.payload.agent_id]: frame.payload,
            },
          };
        case "policy_published":
          return { latestPolicy: frame.payload };
        case "eval_progress":
          return {
            evals: { ...s.evals, [frame.payload.id]: frame.payload },
          };
        case "heartbeat":
          return { lastHeartbeatTs: frame.ts };
      }
    }),

  rehydrate: (snap) =>
    set((s) => ({
      audit: snap.audit ?? s.audit,
      approvals: snap.approvals
        ? Object.fromEntries(snap.approvals.map((a) => [a.id, a]))
        : s.approvals,
      agents: snap.agents
        ? Object.fromEntries(snap.agents.map((a) => [a.agent_id, a]))
        : s.agents,
      evals: snap.evals
        ? Object.fromEntries(snap.evals.map((e) => [e.id, e]))
        : s.evals,
      latestPolicy:
        snap.latestPolicy !== undefined ? snap.latestPolicy : s.latestPolicy,
    })),

  setConnection: (connection) => set({ connection }),

  setDraftPolicy: (draftPolicy) => set({ draftPolicy }),

  updateDraftPolicy: (patch) =>
    set((s) => ({
      draftPolicy: s.draftPolicy ? { ...s.draftPolicy, ...patch } : null,
    })),
}));

export const selectPendingApprovals = (s: StoreState) =>
  Object.values(s.approvals)
    .filter((a) => a.state === "pending")
    .sort((a, b) => a.created_at.localeCompare(b.created_at));

export const selectAgentsList = (s: StoreState) =>
  Object.values(s.agents).sort((a, b) =>
    (a.agent_label ?? a.agent_id).localeCompare(b.agent_label ?? b.agent_id),
  );

export const selectEvalsList = (s: StoreState) =>
  Object.values(s.evals).sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );

export const selectKpis = (s: StoreState) => {
  let allowed = 0;
  let denied = 0;
  let awaiting = 0;
  for (const entry of s.audit) {
    if (entry.decision === "allow") allowed += 1;
    else if (entry.decision === "deny") denied += 1;
    else if (entry.decision === "approval_required") awaiting += 1;
  }
  return {
    allowed,
    denied,
    awaiting,
    activePolicyId: s.latestPolicy?.id ?? null,
    activePolicyName: s.latestPolicy?.name ?? null,
  };
};
