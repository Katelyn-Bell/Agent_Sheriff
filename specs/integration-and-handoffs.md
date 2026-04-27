# AgentSheriff — Integration & Handoffs

This file freezes the shared contracts for the CrabTrap-inspired merge. If a per-person spec disagrees with this file, this file wins.

## How to use this document

1. Read [`_shared-context.md`](_shared-context.md) first.
2. Read this file before implementing any shared DTO, endpoint, stream frame, or env var.
3. Treat the sections below as the contract boundary across People 1 through 4.

## Definition of done

The merged architecture is considered integrated when:

1. A draft policy can be generated from a user intent description.
2. A policy version can be edited, published, and attached to tool-call decisions.
3. `POST /v1/tool-call` runs `heuristics -> static rules -> optional judge -> optional approval -> adapter`.
4. The dashboard renders live audit, approvals, policies, and evals from the real backend.
5. `good`, `injection`, and `approval` still pass as end-to-end scenarios.

---

## 1. Shared ownership map

| Area | Owner | Notes |
|---|---|---|
| Gateway orchestration, DTOs, persistence, REST, WS | Person 1 | Owns the source of truth for API and storage contracts |
| Heuristics, LLM judge helper, starter policy generation inputs, replay evaluator | Person 2 | Supplies signal logic and policy-intelligence helpers |
| Dashboard UX and frontend type mirror | Person 3 | Mirrors backend DTOs exactly |
| Adapters, tool manifest, OpenClaw bridge, demo packaging | Person 4 | Owns executable tool surface and demo runtime |

---

## 2. Canonical nouns

Use these names consistently across specs and code:

- **tool call gateway**: the FastAPI ingress that receives normalized tool actions
- **policy version**: a versioned bundle of static rules and judge prompt
- **static rule**: deterministic allow/deny/approval/judge delegation rule
- **judge prompt**: natural-language instructions for the LLM judge
- **eval run**: replay of prior audit entries against a selected policy version
- **approval request**: a pending human decision attached to a tool call
- **ledger**: the audit history store

Do not use CrabTrap's `proxy request` terminology in MVP docs unless explicitly discussing a future phase.

---

## 3. DTO contract freeze

### `ToolCallRequest`

```json
{
  "agent_id": "deputy-dusty",
  "agent_label": "Deputy Dusty",
  "tool": "gmail.send_email",
  "args": {},
  "context": {
    "task_id": "task-1",
    "source_prompt": "User asked to send the invoice",
    "source_content": "Most recent message or page text",
    "conversation_id": "conv-1"
  }
}
```

Rules:

- `agent_label` is optional on write but should be persisted when supplied.
- `tool` is always a dotted name, for example `gmail.send_email`.
- `args` is an arbitrary JSON object and must be stored in replayable form.
- `context` may hold extra keys; the backend preserves them when useful for audit/eval.

### `ToolCallResponse`

```json
{
  "decision": "allow",
  "reason": "Matched rule policy.default.internal_email",
  "risk_score": 18,
  "matched_rule_id": "policy.default.internal_email",
  "judge_used": false,
  "policy_version_id": "pv_001",
  "audit_id": "audit_001",
  "approval_id": null,
  "user_explanation": null,
  "result": {
    "status": "sent"
  }
}
```

Rules:

- `decision` is `allow`, `deny`, or `approval_required`
- `matched_rule_id` may be null when the judge settled the call
- `judge_used` is required
- `policy_version_id` is required
- `approval_id` is null unless approval is in play
- `result` is present only when the action was executed
- `user_explanation` is optional human-readable text for UI surfaces

### `StaticRule`

```json
{
  "id": "policy.default.block_force_push",
  "name": "Block force pushes",
  "tool_match": {
    "kind": "exact",
    "value": "github.push_branch"
  },
  "arg_predicates": [
    {
      "path": "force",
      "operator": "equals",
      "value": true
    }
  ],
  "action": "deny",
  "severity_floor": 80,
  "stop_on_match": true,
  "reason": "Force-pushes are blocked by default",
  "user_explanation": "This action rewrites git history and is blocked by policy."
}
```

Rules:

- `action` is one of `allow`, `deny`, `require_approval`, `delegate_to_judge`
- evaluation is first-match-wins
- `severity_floor` is optional and clamps the final risk score upward
- `stop_on_match` defaults to `true`

### `PolicyVersion`

```json
{
  "id": "pv_001",
  "name": "Finance assistant",
  "version": 3,
  "status": "published",
  "intent_summary": "This agent triages inbox, drafts updates, and sends internal finance documents for review.",
  "judge_prompt": "You are a conservative security reviewer for tool actions...",
  "static_rules": [],
  "created_at": "2026-04-24T20:00:00Z",
  "published_at": "2026-04-24T20:05:00Z"
}
```

Rules:

- `status` is `draft`, `published`, or `archived`
- publishing a version does not mutate historical audit rows
- audit rows reference the exact `policy_version_id` used at decision time

### `PolicyGenerationRequest`

```json
{
  "name": "Finance assistant",
  "user_intent": "I use OpenClaw to triage finance email, draft notes, and send invoices internally.",
  "tool_manifest": [
    "gmail.read_inbox",
    "gmail.send_email",
    "calendar.create_event",
    "files.read"
  ]
}
```

### `PolicyGenerationResponse`

```json
{
  "intent_summary": "Finance inbox assistant focused on internal communications and document handling.",
  "judge_prompt": "Default judge prompt ...",
  "static_rules": [],
  "notes": [
    "External recipients require review",
    "Sensitive attachments default to approval"
  ]
}
```

### `EvalRun`

```json
{
  "id": "eval_001",
  "policy_version_id": "pv_002",
  "status": "running",
  "created_at": "2026-04-24T20:10:00Z",
  "completed_at": null,
  "total_entries": 125,
  "processed_entries": 33,
  "agreed": 24,
  "disagreed": 7,
  "errored": 2
}
```

### `EvalResult`

```json
{
  "id": "er_001",
  "eval_run_id": "eval_001",
  "audit_id": "audit_321",
  "original_decision": "deny",
  "replayed_decision": "allow",
  "matched_rule_id": null,
  "judge_used": true,
  "replay_reason": "The draft policy no longer blocks external attachment sends.",
  "agreement": false
}
```

### `ApprovalDTO`

```json
{
  "id": "approval_001",
  "state": "pending",
  "agent_id": "deputy-dusty",
  "agent_label": "Deputy Dusty",
  "tool": "gmail.send_email",
  "args": {
    "to": "accountant@example.com"
  },
  "reason": "Sensitive attachment requires review",
  "created_at": "2026-04-24T20:02:00Z",
  "expires_at": "2026-04-24T20:04:00Z",
  "policy_version_id": "pv_001"
}
```

`ApprovalState` is frozen as:

- `pending`
- `approved`
- `denied`
- `redacted`
- `timed_out`

---

## 4. REST endpoints

### Gateway

- `POST /v1/tool-call`

### Policies

- `GET /v1/policies`
- `POST /v1/policies`
- `GET /v1/policies/{id}`
- `PUT /v1/policies/{id}`
- `POST /v1/policies/{id}/publish`
- `POST /v1/policies/generate`

### Evals

- `GET /v1/evals`
- `POST /v1/evals`
- `GET /v1/evals/{id}`
- `GET /v1/evals/{id}/results`

### Audit

- `GET /v1/audit?limit=&agent_id=&decision=&policy_version_id=&since=`

### Approvals

- `GET /v1/approvals?state=pending`
- `POST /v1/approvals/{id}`

### Agents

- `GET /v1/agents`
- `POST /v1/agents/{id}/jail`
- `POST /v1/agents/{id}/release`
- `POST /v1/agents/{id}/revoke`

### Health

- `GET /health`

---

## 5. Stream frame contract

`WS /v1/stream` pushes discriminated frames:

```json
{ "type": "audit", "payload": { } }
{ "type": "approval", "payload": { } }
{ "type": "agent_state", "payload": { } }
{ "type": "policy_published", "payload": { } }
{ "type": "eval_progress", "payload": { } }
{ "type": "heartbeat", "ts": 1713999999 }
```

Rules:

- frontend treats `type` as the discriminant
- no client messages are required for steady-state operation
- `eval_progress` should be sufficient to update a progress UI without polling

---

## 6. Evaluation order

The backend and all dependent specs must assume this exact decision order:

1. validate the tool name against the adapter manifest
2. normalize the request
3. compute heuristic signals and score
4. load the active policy version
5. evaluate static rules in order
6. if the matched rule says `allow`, `deny`, or `require_approval`, settle accordingly
7. if the rule says `delegate_to_judge`, or no rule matches, call the LLM judge
8. if the judge says `require_approval`, enqueue approval
9. if execution is allowed, call `DISPATCH`
10. persist audit row and stream updates

This ordering is intentionally closer to CrabTrap's rule-first shape, while keeping AgentSheriff approvals.

---

## 7. Env vars

| Var | Owner | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | P1 | `sqlite+aiosqlite:///./sheriff.db` | SQLite for MVP |
| `ANTHROPIC_API_KEY` | P1/P2 | unset | Enables judge path when present |
| `USE_LLM_CLASSIFIER` | P2 | `1` | `0` forces rules-only mode |
| `FRONTEND_ORIGIN` | P1 | `http://localhost:3000` | CORS |
| `APPROVAL_TIMEOUT_S` | P1 | `300` | Approval expiry |
| `GATEWAY_ADAPTER_SECRET` | P1/P4 | unset | Required at startup |
| `AGENTSHERIFF_MOCK_FS` | P4 | `./mock-fs` | Mock adapter root |
| `AGENTSHERIFF_BASE_URL` | P2 | `http://localhost:8000` | Dusty base URL |
| `NEXT_PUBLIC_API_BASE` | P3 | `http://localhost:8000` | Frontend API base |
| `NEXT_PUBLIC_WS_URL` | P3 | `ws://localhost:8000/v1/stream` | Frontend stream URL |

---

## 8. Cross-person implementation handoffs

### Person 1 to Person 2

Person 1 provides:

- DTO names and wire format
- policy version lookup contract
- audit replay input shape

Person 2 provides:

- heuristic signal taxonomy
- judge request/response helper
- starter policy generation helper
- eval replay comparison helpers

### Person 1 to Person 3

Person 1 provides:

- final backend DTOs
- REST endpoint shapes
- stream frame union

Person 3 must mirror these exactly in frontend types.

### Person 1 to Person 4

Person 1 provides:

- `DISPATCH` invocation contract
- tool name validation rules
- gateway token semantics

Person 4 provides:

- canonical tool manifest
- adapter-owned supported tools
- deterministic execution outputs

### Person 2 to Person 3

Person 2 provides:

- user-facing risk and judge explanation fields
- eval result semantics

### Person 2 to Person 4

Person 2 provides:

- scenario fixtures and starter policy generation assumptions

### Person 3 to Person 4

Person 3 provides:

- UI expectations for adapter result summaries only, not adapter internals

---

## 9. Acceptance matrix

### Product flow

1. Generate a starter policy from a free-text intent description.
2. Publish the generated policy.
3. Run a normal allowed tool call.
4. Run a denied exfiltration-style tool call.
5. Run an approval-required tool call.
6. Run an eval against recent ledger entries.

### Demo flow

The existing `good`, `injection`, and `approval` scenarios must still pass through the new contracts without forking DTO shapes.

---

## 10. Open issues explicitly deferred

These are acknowledged but not part of the MVP contract freeze:

- HTTP MITM proxy support
- per-user auth and tenancy
- Postgres migration path
- response filtering and WebSocket frame inspection
- multi-agent policy assignment beyond a single local operator flow
