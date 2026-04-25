import type {
  AgentStateDTO,
  ApprovalDTO,
  ApprovalResolution,
  AuditEntryDTO,
  AuditQuery,
  EvalRunDTO,
  EvalResultDTO,
  HealthResponse,
  PolicyGenerationRequest,
  PolicyGenerationResponse,
  PolicyVersionDTO,
  SkillDTO,
  SkillLawGenerationRequest,
  ToolDefinitionDTO,
  ToolCallRequest,
  ToolCallResponse,
  UserDTO,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type FetchOpts = {
  method?: string;
  body?: unknown;
  query?: Record<string, unknown>;
  signal?: AbortSignal;
};

async function apiFetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const { method = "GET", body, query, signal } = opts;
  const url = new URL(path, API_BASE);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  const text = await res.text();
  const parsed = text ? safeJson(text) : undefined;
  if (!res.ok) {
    throw new ApiError(
      res.status,
      parsed,
      `${method} ${path} → ${res.status}`,
    );
  }
  return parsed as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

// Gateway
export const postToolCall = (req: ToolCallRequest, signal?: AbortSignal) =>
  apiFetch<ToolCallResponse>("/v1/tool-call", {
    method: "POST",
    body: req,
    signal,
  });

// Policies
export const listPolicies = (signal?: AbortSignal) =>
  apiFetch<PolicyVersionDTO[]>("/v1/policies", { signal });

export const getPolicy = (id: string, signal?: AbortSignal) =>
  apiFetch<PolicyVersionDTO>(`/v1/policies/${id}`, { signal });

export const createPolicy = (policy: Partial<PolicyVersionDTO>) =>
  apiFetch<PolicyVersionDTO>("/v1/policies", {
    method: "POST",
    body: policy,
  });

export const updatePolicy = (id: string, policy: Partial<PolicyVersionDTO>) =>
  apiFetch<PolicyVersionDTO>(`/v1/policies/${id}`, {
    method: "PUT",
    body: policy,
  });

export const publishPolicy = (id: string) =>
  apiFetch<PolicyVersionDTO>(`/v1/policies/${id}/publish`, {
    method: "POST",
  });

export const generatePolicy = (req: PolicyGenerationRequest) =>
  apiFetch<PolicyGenerationResponse>("/v1/policies/generate", {
    method: "POST",
    body: req,
  });

// Tools
export const listTools = (signal?: AbortSignal) =>
  apiFetch<ToolDefinitionDTO[]>("/v1/tools", { signal });

// Skills
export const listSkills = (signal?: AbortSignal) =>
  apiFetch<SkillDTO[]>("/v1/skills", { signal });

export const getSkill = (id: string, signal?: AbortSignal) =>
  apiFetch<SkillDTO>(`/v1/skills/${id}`, { signal });

export const generateSkillLaws = (
  id: string,
  req: SkillLawGenerationRequest,
) =>
  apiFetch<PolicyGenerationResponse>(`/v1/skills/${id}/generate-laws`, {
    method: "POST",
    body: req,
  });

// Evals
export const listEvals = (signal?: AbortSignal) =>
  apiFetch<EvalRunDTO[]>("/v1/evals", { signal });

export const createEval = (policy_version_id: string) =>
  apiFetch<EvalRunDTO>("/v1/evals", {
    method: "POST",
    body: { policy_version_id },
  });

export const getEval = (id: string, signal?: AbortSignal) =>
  apiFetch<EvalRunDTO>(`/v1/evals/${id}`, { signal });

export const getEvalResults = (id: string, signal?: AbortSignal) =>
  apiFetch<EvalResultDTO[]>(`/v1/evals/${id}/results`, { signal });

// Audit
export const listAudit = (q: AuditQuery = {}, signal?: AbortSignal) =>
  apiFetch<AuditEntryDTO[]>("/v1/audit", { query: { ...q }, signal });

// Approvals
export const listApprovals = (
  state: ApprovalDTO["state"] = "pending",
  signal?: AbortSignal,
) =>
  apiFetch<ApprovalDTO[]>("/v1/approvals", {
    query: { state },
    signal,
  });

export const resolveApproval = (id: string, action: ApprovalResolution) =>
  apiFetch<ApprovalDTO>(`/v1/approvals/${id}`, {
    method: "POST",
    body: { action },
  });

// Agents
export const listAgents = (signal?: AbortSignal) =>
  apiFetch<AgentStateDTO[]>("/v1/agents", { signal });

export const jailAgent = (id: string) =>
  apiFetch<AgentStateDTO>(`/v1/agents/${id}/jail`, { method: "POST" });

export const releaseAgent = (id: string) =>
  apiFetch<AgentStateDTO>(`/v1/agents/${id}/release`, { method: "POST" });

export const revokeAgent = (id: string) =>
  apiFetch<AgentStateDTO>(`/v1/agents/${id}/revoke`, { method: "POST" });

// Demo (scenario trigger — not in integration-and-handoffs.md endpoint freeze;
// backend needs to implement POST /v1/demo/run for demo-launcher buttons).
export type DemoScenario = "good" | "injection" | "approval";

export const runDemoScenario = (scenario: DemoScenario) =>
  apiFetch<{ status: string; task_id?: string }>("/v1/demo/run", {
    method: "POST",
    body: { scenario },
  });

// Auth
export const getMe = (signal?: AbortSignal) =>
  apiFetch<UserDTO>("/v1/auth/me", { signal });

export const logout = () =>
  apiFetch<void>("/v1/auth/logout", { method: "POST" });

export const GOOGLE_SIGNIN_URL = `${API_BASE}/v1/auth/google/start`;

// Health
export const getHealth = () => apiFetch<HealthResponse>("/health");

export const API_BASE_URL = API_BASE;
