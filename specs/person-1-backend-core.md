# Person 1 — Backend Core Spec

> Owner: Person 1
> Primary directories: `backend/src/agentsheriff/` and `backend/tests/`
> Read [`specs/_shared-context.md`](./_shared-context.md) and [`specs/integration-and-handoffs.md`](./integration-and-handoffs.md) first.

## Mission

Build the local tool-call gateway that turns AgentSheriff into a general-purpose policy layer for agents.

You own the backend source of truth for:

- wire DTOs
- gateway orchestration
- policy version persistence
- approval queue
- audit ledger
- replay eval APIs
- WebSocket stream frames

You do **not** own:

- threat heuristics internals or starter-policy generation logic beyond the interface boundary
- dashboard implementation
- adapter business logic

## Architecture you are implementing

The gateway decision order is frozen:

1. validate tool name
2. normalize request
3. compute heuristic signals
4. load the active published policy version
5. evaluate static rules in order
6. if unresolved, call the LLM judge helper
7. if policy or judge requires approval, enqueue approval and block on resolution
8. if allowed, dispatch to the adapter layer
9. persist audit row and stream updates

## Deliverables

Create or update these modules:

```text
backend/src/agentsheriff/
├── main.py
├── config.py
├── gateway.py
├── streams.py
├── models/
│   ├── dto.py
│   └── orm.py
├── policy/
│   ├── engine.py
│   ├── store.py
│   ├── builder.py
│   └── templates/
├── audit/
│   └── store.py
├── approvals/
│   └── queue.py
├── api/
│   ├── tool_calls.py
│   ├── policies.py
│   ├── audit.py
│   ├── approvals.py
│   ├── agents.py
│   ├── evals.py
│   └── health.py
└── tests/
    ├── test_gateway.py
    ├── test_policies.py
    └── test_evals.py
```

## 1. Settings and runtime

### Required env vars

- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `APPROVAL_TIMEOUT_S`
- `GATEWAY_ADAPTER_SECRET`

### Optional env vars

- `ANTHROPIC_API_KEY`
- `USE_LLM_CLASSIFIER`
- `LOG_LEVEL`
- `POLICY_PATH`

### MVP constraints

- FastAPI + SQLite stay in place
- structured JSON logging
- no auth for MVP
- SQLite WAL mode enabled
- backend must remain functional when `USE_LLM_CLASSIFIER=0`

## 2. DTOs you own

The frontend mirrors these by hand. Do not rename casually.

### Core enums

- `Decision`: `allow | deny | approval_required`
- `ApprovalState`: `pending | approved | denied | redacted | timed_out`
- `PolicyStatus`: `draft | published | archived`
- `EvalStatus`: `pending | running | completed | failed | cancelled`

### Core request and response models

Implement at minimum:

- `ToolCallContext`
- `ToolCallRequest`
- `ToolCallResponse`
- `StaticRuleDTO`
- `PolicyVersionDTO`
- `PolicyGenerationRequest`
- `PolicyGenerationResponse`
- `ApprovalDTO`
- `AuditEntryDTO`
- `EvalRunDTO`
- `EvalResultDTO`
- stream frame union types

### Required `ToolCallResponse` fields

```python
decision: Decision
reason: str
risk_score: int
matched_rule_id: str | None
judge_used: bool
policy_version_id: str
audit_id: str
approval_id: str | None = None
user_explanation: str | None = None
result: dict[str, Any] | None = None
```

### Required `AuditEntryDTO` fields

```python
id: str
ts: str
agent_id: str
agent_label: str | None
tool: str
args: dict[str, Any]
context: dict[str, Any]
decision: Decision
risk_score: int
reason: str
matched_rule_id: str | None
judge_used: bool
judge_rationale: str | None
policy_version_id: str
approval_id: str | None
execution_summary: dict[str, Any] | None
user_explanation: str | None
```

## 3. ORM and persistence

### Required tables

- `agents`
- `policy_versions`
- `audit_entries`
- `approvals`
- `eval_runs`
- `eval_results`

### `policy_versions` requirements

Store:

- version metadata
- `intent_summary`
- `judge_prompt`
- serialized `static_rules`
- status and timestamps

Historical policy versions must remain immutable after publish except for archival metadata.

### `audit_entries` requirements

This table is both the ledger and the replay source for evals. It must persist:

- full normalized request
- heuristic summary
- matched rule id
- whether the judge ran
- judge rationale
- decision
- approval metadata
- execution summary
- policy version id

The audit row must be sufficient to replay the decision later without querying the original adapter output again.

### `eval_runs` and `eval_results`

`eval_runs` stores aggregate progress.

`eval_results` stores one replay result per audit row, including:

- original decision
- replayed decision
- matched rule id
- judge usage
- replay reason
- agreement boolean

## 4. Policy engine

Implement `policy/engine.py` as a deterministic evaluator over ordered static rules.

### Rule semantics

Each rule supports:

- `tool_match.kind`: `exact | namespace`
- `tool_match.value`
- optional `arg_predicates`
- `action`: `allow | deny | require_approval | delegate_to_judge`
- optional `severity_floor`
- `reason`
- `user_explanation`
- `stop_on_match`

### Evaluation behavior

- first match wins
- default when no rule matches: `delegate_to_judge`
- `severity_floor` clamps the final risk score upward
- rule evaluation must be side-effect free

## 5. Policy store and versioning

Implement `policy/store.py` with these responsibilities:

- create draft policy version
- list versions
- load by id
- load active published version
- update draft version
- publish version
- archive version

Publishing a version should be explicit. Do not mutate prior published versions in place.

## 6. Policy generation endpoint

`POST /v1/policies/generate` is a backend-owned API that delegates generation logic to Person 2's helper.

The backend is responsible for:

- request validation
- passing the tool manifest and user intent to the generator
- returning a draft-shaped payload
- not auto-publishing generated output

The backend does **not** own the quality of the generated rules. It owns the API seam and persistence shape.

## 7. Gateway orchestration

Implement `gateway.py` to orchestrate the full flow.

### Inputs

- `ToolCallRequest`
- active published policy version
- heuristic report from Person 2
- optional judge result from Person 2
- adapter manifest from Person 4

### Required branches

#### Unknown tool

Return deny with a clear reason before any adapter call.

#### Static rule settles

Use the rule action directly, unless approval is required.

#### Judge path

If rules delegate to the judge, call the judge helper with:

- active policy version
- normalized request
- heuristic report

The judge helper must be able to respond with:

- `allow`
- `deny`
- `require_approval`
- rationale text
- user explanation
- optional severity recommendation

#### Approval path

When approval is required:

1. enqueue approval
2. stream a pending approval frame
3. await resolution
4. if approved or redacted, continue execution
5. if denied or timed out, return deny and persist audit accordingly

#### Allow path

Dispatch through `DISPATCH[tool]` with `gateway_token=settings.GATEWAY_ADAPTER_SECRET`.

## 8. Approvals queue

Implement `approvals/queue.py` with:

- in-memory pending map for MVP
- expiration via `APPROVAL_TIMEOUT_S`
- states `pending`, `approved`, `denied`, `redacted`, `timed_out`
- resume semantics for the blocked gateway request

`redacted` means the backend applies a server-side scrub to sensitive arguments before execution. The client may request redaction, but the backend owns the transformation.

## 9. Eval system

Implement `api/evals.py` and the underlying service path.

### `POST /v1/evals`

Creates a new eval run over a selected policy version and an audit query filter.

### Eval execution model

- async background task is acceptable for MVP
- process audit rows in batches
- write incremental progress to `eval_runs`
- emit `eval_progress` stream frames

### Replay logic

For each audit row:

1. rebuild the policy evaluation context from stored fields
2. rerun static rules
3. rerun the judge only if the policy would delegate to it
4. compare the replayed decision to the original
5. persist the result

## 10. REST surface you own

### Tool calls

- `POST /v1/tool-call`

### Policies

- `GET /v1/policies`
- `POST /v1/policies`
- `GET /v1/policies/{id}`
- `PUT /v1/policies/{id}`
- `POST /v1/policies/{id}/publish`
- `POST /v1/policies/generate`

### Audit

- `GET /v1/audit?limit=&agent_id=&decision=&policy_version_id=&since=`

### Approvals

- `GET /v1/approvals?state=`
- `POST /v1/approvals/{id}`

### Evals

- `GET /v1/evals`
- `POST /v1/evals`
- `GET /v1/evals/{id}`
- `GET /v1/evals/{id}/results`

### Agents

- `GET /v1/agents`
- `POST /v1/agents/{id}/jail`
- `POST /v1/agents/{id}/release`
- `POST /v1/agents/{id}/revoke`

### Health

- `GET /health`

## 11. WebSocket frames

Expose `WS /v1/stream` with these frames:

- `audit`
- `approval`
- `agent_state`
- `policy_published`
- `eval_progress`
- `heartbeat`

Person 3 depends on the `type` discriminant being stable.

## 12. Integration contracts

### With Person 2

Import and use:

- heuristic detection
- judge helper
- starter policy generator
- replay comparison helper, if provided

Person 2 should not own your persistence logic or HTTP surface.

### With Person 4

Import and use:

- adapter `DISPATCH`
- tool manifest metadata

Do not hardcode tool names that should come from the manifest except for scenario smoke tests.

## 13. Tests

Write or update:

### `test_gateway.py`

Cover:

- allow via static rule
- deny via static rule
- delegate to judge then allow
- approval-required flow
- unknown tool denial

### `test_policies.py`

Cover:

- draft creation
- publish semantics
- rule evaluation ordering
- `severity_floor`

### `test_evals.py`

Cover:

- eval run creation
- progress updates
- agreement and disagreement cases

## 14. Acceptance criteria

You are done when all of the following are true:

- the backend contract matches `specs/integration-and-handoffs.md`
- a generated draft policy can be created and then published
- `POST /v1/tool-call` uses rules first and the judge second
- approvals work without bypassing the ledger
- evals can replay stored audit rows against a draft or published policy version
- the three existing demo scenarios still work through the new pipeline

## 15. Deferred but documented

Leave explicit TODO markers, not silent omissions, for:

- real auth
- Postgres migration path
- true proxy interception layer
- long-running eval workers beyond the in-process MVP
