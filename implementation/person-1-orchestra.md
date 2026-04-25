# Person 1 — Backend Core (Orchestra Run File)

**Owner:** Person 1
**Working directory:** `/Users/bernardorodrigues/Documents/Code/Agent_Sheriff/backend`
**Branch:** `person-1/backend-core`
**Spec:** [`../specs/person-1-backend-core.md`](../specs/person-1-backend-core.md)
**Shared context:** [`../specs/_shared-context.md`](../specs/_shared-context.md)
**Integration contract:** [`../specs/integration-and-handoffs.md`](../specs/integration-and-handoffs.md)

## How to use this file

Each Run is a delivery checkpoint. Finish the Run, verify it, push it, then move to the next one. Agents listed inside a Run may work in parallel only when they touch disjoint files or stable seams.

## Mission

Person 1 builds the local tool-call gateway: DTOs, policy storage, static-rule evaluation, approval flow, audit ledger, replay eval APIs, and live stream frames.

## Assumptions

- Python 3.11 and `uv` are installed.
- `GATEWAY_ADAPTER_SECRET` is set in every backend shell.
- SQLite remains the MVP store.
- Person 2 supplies heuristics, judge, generator, and replay-comparison helpers.
- Person 4 supplies `DISPATCH` and the tool manifest.

---

## Run 1 — Backend skeleton and frozen contracts

**Purpose.** Create the backend scaffold that unblocks the rest of the team and freezes the wire contract in code.

### Agent 1A — Scaffold backend package, DTOs, ORM, and health route

Read the backend spec sections on settings, DTOs, and persistence. Create the package tree under `backend/src/agentsheriff/` and implement:

- `config.py`
- `models/dto.py`
- `models/orm.py`
- `main.py`
- `api/health.py`

Make sure `ToolCallRequest`, `ToolCallResponse`, `PolicyVersionDTO`, `ApprovalDTO`, `AuditEntryDTO`, `EvalRunDTO`, `EvalResultDTO`, and the stream-frame union all match the integration doc. Enable SQLite WAL mode and structured JSON logging.

**Acceptance**

- `uv run uvicorn agentsheriff.main:app --port 8000` boots
- `curl -s localhost:8000/health` returns `{"status":"ok"}`
- DTO imports succeed from a one-line Python smoke test

### Agent 1B — Stub REST routes and stream hub

Implement typed stub handlers for:

- `POST /v1/tool-call`
- `GET /v1/policies`
- `POST /v1/policies`
- `POST /v1/policies/generate`
- `GET /v1/audit`
- `GET /v1/evals`
- `GET /v1/approvals`
- `GET /v1/agents`
- `WS /v1/stream`

Return hard-coded but correctly shaped responses so Person 3 can wire the frontend against real contracts immediately.

**Acceptance**

- all endpoints return 200 with correctly shaped JSON
- `WS /v1/stream` accepts a connection and emits heartbeat frames

---

## Run 2 — Policy versions, rule engine, and gateway path

**Purpose.** Replace stubs with the real policy-version and rule-first decision flow.

### Agent 2A — Policy store and static-rule evaluator

Implement:

- `policy/store.py`
- `policy/engine.py`
- `api/policies.py`

Support:

- create draft policy version
- list and fetch versions
- update draft version
- publish a version
- archive a version

Static rules must support first-match-wins, `allow`, `deny`, `require_approval`, and `delegate_to_judge`, plus optional `severity_floor`.

**Acceptance**

- can create a draft policy
- can publish it
- static-rule evaluation works in isolation with tests

### Agent 2B — Gateway orchestration over heuristics, rules, and judge

Implement `gateway.py` and `api/tool_calls.py` to run:

1. tool validation
2. normalization
3. `detect_threats`
4. active policy load
5. static rule evaluation
6. optional `judge_tool_call`
7. allow or deny path

Do not wire approvals or adapter execution yet beyond stable stubs. Persist an audit row for every decision.

**Acceptance**

- a static-rule allow returns `decision=allow`
- a static-rule deny returns `decision=deny`
- an unresolved call uses the judge helper and records `judge_used=true`

---

## Run 3 — Approval flow, adapters, and agent state

**Purpose.** Complete the full execution path and make borderline actions resumable through approval.

### Agent 3A — Approvals queue and approval endpoints

Implement:

- `approvals/queue.py`
- `api/approvals.py`

Support:

- pending approval creation
- timeout handling
- approve, deny, redact resolution
- server-side redaction transform

**Acceptance**

- a `require_approval` action blocks the request
- a POST to `/v1/approvals/{id}` resolves the blocked call
- timed-out approvals become `timed_out`

### Agent 3B — Adapter dispatch and agent-state operations

Wire `DISPATCH` into the allow path and implement:

- `api/agents.py`
- agent jail / release / revoke transitions
- `agent_state` stream events

**Acceptance**

- allowed calls execute adapters and attach `result`
- jailed agents appear in `/v1/agents`
- release returns them to active state

---

## Run 4 — Replay eval system

**Purpose.** Turn the ledger into a replayable source of policy testing.

### Agent 4A — Eval persistence and async execution

Implement:

- `api/evals.py`
- eval run creation
- row replay loop
- progress persistence
- `eval_progress` stream events

Replay each audit row against a selected policy version using the stored normalized request and context.

**Acceptance**

- `POST /v1/evals` creates a run
- progress updates stream live
- `GET /v1/evals/{id}` and `/results` return aggregates and rows

### Agent 4B — Audit query improvements for replay and UI

Finish `audit/store.py` and `api/audit.py` so the ledger supports:

- filtering by decision, agent, policy version, and time
- row shapes rich enough for replay and UI drill-down

**Acceptance**

- audit rows include matched rule id, judge usage, approval id, and execution summary
- ledger filters work through the REST API

---

## Run 5 — Integration hardening

**Purpose.** Make the backend stable against real frontend, heuristics, and adapters.

### Agent 5A — Full backend test pass and error normalization

Add or finish:

- `test_gateway.py`
- `test_policies.py`
- `test_evals.py`
- global error envelope normalization

Normalize errors to:

```json
{"error":{"code":"UPPER_SNAKE","message":"Human readable"}}
```

**Acceptance**

- backend tests pass
- error envelope is consistent
- logs stay structured and secret-clean

---

## Cross-team handoffs

- **To Person 2:** stable DTOs and policy-version context
- **To Person 3:** final REST shapes and stream union
- **To Person 4:** gateway invocation contract for `DISPATCH`

---

## Final acceptance

Person 1 is done when all of these are true:

1. `POST /v1/tool-call` runs rules first and judge second.
2. approvals work end to end.
3. audit rows are replayable.
4. eval runs execute and stream progress.
5. the `good`, `injection`, and `approval` scenarios pass through the real backend.

**Purpose.** Stand up the backend skeleton so every other person can import the package and hit a live `/health`. Everything in this Run is deliberately fake-but-typed: real DTOs, real ORM, stub business logic — so P2/P3/P4 can wire against frozen seams while real implementations land in Run 2.
**Dependencies.** None.
**Parallel agents.** 1.

### Agent 1A — Scaffold backend, DTOs, ORM, stub endpoints + stub threats + stub DISPATCH (incl. calendar)

You are bootstrapping the AgentSheriff backend. Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-1-backend-core.md` sections 1, 2, 3, 10, 13 and `/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md` §1 and §7 (Fixes #1, #4, #8) before writing code. The integration doc is authoritative when it disagrees with the per-person spec.

Create the branch `person-1/backend-core` off `main`. Inside `/Users/ianrowe/git/Agent_Sheriff/backend`, run `uv init --package` and write a `pyproject.toml` pinning fastapi, uvicorn[standard], pydantic>=2, pydantic-settings, sqlalchemy>=2, aiosqlite, pyyaml, anthropic, python-json-logger, httpx, pytest, pytest-asyncio. Build the package tree under `src/agentsheriff/` per spec §1 layout.

Implement `models/dto.py` with **every reconciled DTO** from integration §7 Fix #1: ApprovalState enum must include `pending|approved|denied|timed_out|redacted`; ApprovalDTO carries `created_at`, `expires_at`, `agent_label`, `user_explanation`; AuditEntryDTO carries `agent_label` and `user_explanation`; AgentDTO carries `requests_today` and `blocked_today`; ToolCallResponse carries `user_explanation`. Use the discriminated stream-frame union from §2.

Implement `models/orm.py` with an `engine` that fires `PRAGMA journal_mode=WAL` on connect via a SQLAlchemy `event.listens_for("connect")` hook, plus an async `session_factory`. Implement `config.py` (pydantic-settings) with `GATEWAY_ADAPTER_SECRET` as required, fail-fast at import. Implement `main.py` with full CORS (FRONTEND_ORIGIN env + literal `http://localhost:3000`), python-json-logger, and a log filter that redacts any key matching `*SECRET*|*API_KEY*|*TOKEN*`.

Stub `api/agents.py`, `api/policies.py`, `api/approvals.py`, `api/audit.py`, `api/health.py`, `api/demo.py` returning hard-coded fixture data shaped exactly like the DTOs. Stub `threats/__init__.py` exposing `detect()` returning an empty `ThreatReport` and `classifier.classify_async()` returning `injection=False, confidence=0.0`. Stub `adapters/__init__.py` exposing a `DISPATCH` dict for **all six namespaces** including `calendar` (gmail, gdrive, slack, github, calendar, notion), each pointing to an async no-op returning `{"ok": true, "stub": true}`.

**Acceptance.** `uv run uvicorn agentsheriff.main:app --port 8000` boots; `curl -s localhost:8000/health` returns `{"status":"ok"}`; `uv run python -c "from agentsheriff.adapters import DISPATCH; from agentsheriff.threats import detect; from agentsheriff.models.dto import ApprovalState; assert 'calendar' in DISPATCH and ApprovalState.timed_out and ApprovalState.redacted"` exits 0.

**Verification.** Run both commands above. Push the branch and open a draft PR titled `Person 1 — Backend Core (WIP)` referencing `specs/person-1-backend-core.md`.

**Exit criteria for Run 1.**
- Backend boots cleanly under `uv run uvicorn`.
- `GET /health` returns 200 with JSON body.
- All six adapter namespaces (incl. `calendar`) import; `DISPATCH` is a dict.
- `ApprovalState` enum has `timed_out` and `redacted` members.
- Branch pushed; draft PR open.

---

## Run 2 — Gateway pipeline + policy engine + audit store (H2→H6)

**Purpose.** Replace the stubbed `/v1/tool-call` and supporting state with real orchestration. By the end of Run 2, the `good` scenario allows and the `injection` scenario denies + jails via the `jail_on_deny` policy field.
**Dependencies.** Run 1 merged (or branch up-to-date).
**Parallel agents.** 2.

### Agent 2A — Gateway + policy engine + 4 YAML templates

Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-1-backend-core.md` §4 and §5 in full, plus `specs/integration-and-handoffs.md` §7 Fix #2 (approval-on-attachment), Fix #4 (gateway secret), Fix #12 (redact semantics). Branch `person-1/backend-core`.

Implement `policy/engine.py`: YAML loader, first-match-wins evaluator over the rule list, hot reload via mtime check on every evaluate call. The Rule schema includes `match`, `action` (`allow|deny|approval`), `risk_floor` (used to clamp risk on prompt-injection matches before subsequent rules run), and **`jail_on_deny: bool`**. The shared `SENSITIVE_FILE_RE` regex must match the wording Person 2 uses in `threats/detector.py` and must include the tokens `invoice|employees|customers` alongside the existing salary/passport/payroll/confidential set.

Implement `gateway.py` (`POST /v1/tool-call`) orchestrating: agent lookup/upsert → threats.detect → optional `classifier.classify_async` (gated by `USE_LLM_CLASSIFIER`) → policy.evaluate → DISPATCH (passing `GATEWAY_ADAPTER_SECRET` via `secrets.compare_digest` contract per Fix #4) → finalize ToolCallResponse including `user_explanation` from the matched rule. On `deny` with `jail_on_deny: true`, call `audit.mark_agent_jailed`. Stream every decision as an audit frame.

Write all four templates under `policy/templates/`: `default.yaml`, `healthcare.yaml`, `finance.yaml`, `startup.yaml`. The default template **must** order rules so that `approval-on-attachment` (matches any tool with `attachments` field whose name hits `SENSITIVE_FILE_RE`) fires **before** `gmail-external-needs-approval`, and the `prompt-injection` rule sets `risk_floor: 85` and `jail_on_deny: true`.

**Acceptance.** With backend running: the `good` payload from `specs/_shared-context.md` §scenarios returns `decision=allow, risk=0`; the `injection` payload returns `decision=deny, risk>=85, policy=no-external-pii` and a follow-up `GET /v1/agents` shows that agent `state=jailed`.

**Verification.**
```bash
curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' -d @specs/fixtures/good.json | jq -e '.decision=="allow" and .risk==0'
curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' -d @specs/fixtures/injection.json | jq -e '.decision=="deny" and .risk>=85 and .policy=="no-external-pii"'
curl -s localhost:8000/v1/agents | jq -e '.[] | select(.id==<injection_agent>) | .state=="jailed"'
```

### Agent 2B — Audit store + agents REST + today-counters

Read `specs/person-1-backend-core.md` §3, §6, §9.1 and integration §7 Fix #1 (AgentDTO `requests_today`/`blocked_today`). Branch `person-1/backend-core`.

Implement `audit/store.py` over the async `session_factory`: `record_audit(...)`, `upsert_agent(...)`, `mark_agent_jailed(id)`, `mark_agent_revoked(id)`, `release_agent(id)`, `list_audit(decision=None, since=None, agent_id=None, limit=200)` (joins `agent_label` from agents table), and `today_counters_for(agent_ids)` returning a dict keyed by id with `requests_today` and `blocked_today` computed from `created_at >= utc_midnight()`.

Implement `api/agents.py`: `GET /v1/agents` enriches each AgentDTO with the today-counters; `POST /v1/agents/{id}/jail`, `/revoke`, `/release` mutate state and emit a `agent_state` WS frame via the streams module (which Agent 3B will own — for now write to a thin module-level pub/sub seam that 3B can replace without touching this file). Coordinate with 2A: gateway calls `mark_agent_jailed` on `jail_on_deny`, your endpoints expose the same transitions for manual ops.

**Acceptance.** After running the `good` and `injection` scenarios twice each, `GET /v1/agents` returns rows where `requests_today >= 2` for the good agent and `blocked_today >= 2` for the injection agent. `POST /v1/agents/{id}/release` flips a jailed agent back to `active`.

**Verification.**
```bash
curl -s localhost:8000/v1/agents | jq -e '.[] | select(.requests_today>=2)'
curl -s -XPOST localhost:8000/v1/agents/<id>/release | jq -e '.state=="active"'
```

**Exit criteria for Run 2.**
- `good` curl → allow; `injection` curl → deny+jailed.
- `default.yaml` lists `approval-on-attachment` strictly before `gmail-external-needs-approval`.
- `requests_today` / `blocked_today` populated on `GET /v1/agents`.
- All edits squash-mergeable onto `main`.

---

## Run 3 — Approvals + WebSocket + remaining REST (H6→H10)

**Purpose.** Stand up the approval flow, the live WebSocket multiplexer, and every remaining REST endpoint so the dashboard can light up end-to-end. Approval scenario must work both terminals.
**Dependencies.** Run 2.
**Parallel agents.** 3.

### Agent 3A — Approvals queue + redact + gateway approval path

Read `specs/person-1-backend-core.md` §7 and integration §7 Fix #12 (redact semantics) and §2.3 (approval flow). Branch `person-1/backend-core`.

Implement `approvals/queue.py`: an in-memory dict of `id -> ApprovalRecord` plus `asyncio.Event` per record. API: `create(agent_id, tool_namespace, tool_name, args, user_explanation) -> ApprovalDTO` (sets `created_at=now`, `expires_at=now + APPROVAL_TIMEOUT_S` where the env default is 120), `await_resolution(id, timeout=APPROVAL_TIMEOUT_S) -> ResolvedApproval`, `resolve(id, action, scope, redacted_args=None)`. On timeout, transition to `timed_out` and broadcast.

Add `_redact_args(args, fields)` helper (server-side; never trust the client's redacted payload — the client only sends `{action: "redact", scope: {fields: [...]}}` and the server scrubs). Resolution paths: `approved` → gateway dispatches the original args; `denied` → gateway returns deny; `redacted` → gateway dispatches with `_redact_args` applied; `timed_out` → gateway returns deny with `policy="approval-timeout"`.

Implement `api/approvals.py`: `POST /v1/approvals/{id}` accepting `{action, scope?}`, `GET /v1/approvals?state=pending`. Wire the gateway approval branch: when policy returns `approval`, enqueue via `queue.create(...)`, broadcast an `approval_request` WS frame, `await_resolution`, then dispatch / deny / redact accordingly.

**Acceptance.** Two-terminal dance: terminal A `curl -s localhost:8000/v1/tool-call -d @specs/fixtures/approval.json` blocks; terminal B `curl -s localhost:8000/v1/approvals?state=pending | jq '.[0].id'` returns the id; terminal B `curl -s -XPOST localhost:8000/v1/approvals/<id> -d '{"action":"approved"}'` resolves; terminal A unblocks within 1 second with `decision=allow`.

**Verification.** Run the dance above; assert `decision=="allow"` on terminal A's response.

### Agent 3B — WebSocket multiplexer with heartbeat

Read `specs/person-1-backend-core.md` §8 and `specs/_shared-context.md` "WS /v1/stream". Branch `person-1/backend-core`.

Implement `streams.py` with a `Hub` singleton: per-connection `asyncio.Queue`, `register(ws)` / `unregister(ws)`, `broadcast(frame_dict)`. `WS /v1/stream` accepts the connection, registers, and runs **only a server-push loop** — no `await ws.receive_text()` loop, because the frontend uses `react-use-websocket` which would conflict with bidirectional draining. Push a `{"type":"heartbeat","ts":<unix>}` frame every 5 seconds. Catch `WebSocketDisconnect` and unregister cleanly.

Replace the seam Agent 2B left for agent-state events; wire `gateway.py` and `approvals/queue.py` to call `Hub.broadcast(...)` for `audit`, `approval_request`, `approval_resolved`, and `agent_state` frames. Use the discriminated-union DTOs from `models/dto.py` so frames serialize with the `type` discriminator the frontend expects.

**Acceptance.** `websocat ws://localhost:8000/v1/stream` shows a heartbeat within 5s; running the `good` scenario causes an `audit` frame to appear on the open socket.

**Verification.**
```bash
( websocat -n1 ws://localhost:8000/v1/stream & sleep 1; curl -s localhost:8000/v1/tool-call -d @specs/fixtures/good.json >/dev/null ; wait )
```
Expect at least one `"type":"audit"` frame and one `"type":"heartbeat"` frame in stdout.

### Agent 3C — Remaining REST (policies, audit, health, demo) + CORS + logging

Read `specs/person-1-backend-core.md` §9.2, §9.4, §9.5, §9.6, §10, §14 and integration §7 Fix #3. Branch `person-1/backend-core`.

Implement `api/policies.py`: `GET /v1/policies` returns the active YAML as text + parsed structure, `PUT /v1/policies` accepts a YAML body, validates by parsing into the engine's Rule model, persists to `policy/active.yaml`, and triggers hot reload. `GET /v1/policies/templates` lists the four template names; `POST /v1/policies/apply-template {name}` copies a template over `active.yaml` and reloads.

Implement `api/audit.py`: `GET /v1/audit` with query filters `decision`, `since` (ISO timestamp), `agent_id`, `limit` — delegates to `audit.store.list_audit`. Implement `api/health.py` returning `{status:"ok", version, started_at}`.

Implement `api/demo.py`: `POST /v1/demo/run/{scenario_id}` validates `scenario_id in {good, injection, approval}` and uses **`asyncio.create_task(run_scenario(...))`** to fire-and-forget the scenario from `agentsheriff.scenarios` (a small in-process module that posts to its own `/v1/tool-call` via `httpx.AsyncClient`). **Do not shell out via subprocess** — the endpoint must return in <100ms.

Confirm `main.py` CORS allows both `os.getenv("FRONTEND_ORIGIN")` and `http://localhost:3000`, and that the secret-redacting log filter scrubs any record with keys matching `*SECRET*|*API_KEY*|*TOKEN*`. Wire all routers.

**Acceptance.** Each documented endpoint returns the shape from §9.7. `POST /v1/demo/run/good` returns 202 in <100ms and the WS sees the resulting audit frame within ~1s.

**Verification.**
```bash
time curl -s -XPOST localhost:8000/v1/demo/run/good -o /dev/null  # < 100ms
curl -s 'localhost:8000/v1/audit?decision=allow&limit=5' | jq 'length'
curl -s localhost:8000/v1/policies/templates | jq 'length==4'
```

**Exit criteria for Run 3.**
- All five verification commands across 3A/3B/3C pass.
- Approval dance resolves in <1s after the operator POSTs.
- WS receives both content and heartbeat frames.
- `GATEWAY_ADAPTER_SECRET` never appears in logs (grep the log file for the secret value → 0 hits).

---

## Run 4 — Real P2/P4 integration + scenario tests (H10→H14)

**Purpose.** Drop the real `agentsheriff.threats` (P2) and real `DISPATCH` (P4) into place, write three async scenario tests, and run a Dusty agent-emulator smoke against the live backend.
**Dependencies.** Run 3 + P2 branch merged + P4 branch merged into `main`.
**Parallel agents.** 1.

### Agent 4A — Swap stubs for real modules + write `test_gateway.py` with 3 scenario tests + Dusty smoke

Read `specs/person-1-backend-core.md` §11, §12, §15 and `specs/integration-and-handoffs.md` §6 (acceptance matrix). Branch `person-1/backend-core` rebased onto current `main` (which now contains real P2 threats and P4 adapters).

Delete the stub files at `src/agentsheriff/threats/detector.py`, `threats/classifier.py`, `threats/__init__.py`, `adapters/_stub.py`, `adapters/gmail.py`, `adapters/calendar.py`, and `adapters/__init__.py` only if they conflict with the merged real modules; otherwise verify the import surface still resolves (`from agentsheriff.threats import detect, classify_async`; `from agentsheriff.adapters import DISPATCH`). Re-run the Run 2 acceptance curls to confirm parity post-swap.

Write `backend/tests/test_gateway.py` using `pytest-asyncio` and `httpx.AsyncClient(app=app, base_url="http://test")`. Three tests, each with `USE_LLM_CLASSIFIER=0` set in env so the heuristic path is deterministic:
1. `test_good_allows`: posts the good fixture, asserts `decision=="allow"`, `risk==0`, `tool_call.executed==True`.
2. `test_injection_denies_and_jails`: posts injection fixture, asserts `decision=="deny"`, `risk>=85`, `policy=="no-external-pii"`; follow-up `GET /v1/agents` asserts the agent's `state=="jailed"`.
3. `test_approval_blocks_then_approves`: uses `asyncio.gather` to race the blocking `POST /v1/tool-call` against a coroutine that polls `GET /v1/approvals?state=pending`, then `POST /v1/approvals/{id} {"action":"approved"}`. Asserts the original call resolves with `decision=="allow"` within 5s.

Run Dusty (`scripts/dusty.py --all`) against the live backend and capture the output table — expect 2 green / 1 red+jailed / 1 amber→approve→green pattern.

**Acceptance.** `uv run pytest backend/tests/test_gateway.py -v` is fully green. Dusty output matches the documented pattern.

**Verification.**
```bash
USE_LLM_CLASSIFIER=0 uv run pytest backend/tests/test_gateway.py -v
python scripts/dusty.py --all
```

Open the PR for review with the pytest output and three demo curl outputs pasted into the description.

**Exit criteria for Run 4.**
- `pytest` green on three scenario tests.
- Dusty `--all` produces the expected 2/1/1 pattern.
- PR open against `main` with verification artifacts in the body.

---

## Run 5 — Hardening & polish (H14→H18)

**Purpose.** Dress-rehearsal fixes, log polish, error-envelope normalization. **No new features.**
**Dependencies.** Run 4 PR open.
**Parallel agents.** 1.

### Agent 5A — Structured logs, error envelope, dress-rehearsal fixes

Read `specs/integration-and-handoffs.md` §6 dress-rehearsal section and `specs/person-1-backend-core.md` §14, §15. Branch `person-1/backend-core`.

Add a global FastAPI exception handler that normalizes all errors to `{"error": {"code": "<UPPER_SNAKE>", "message": "<human readable>"}}`. Map: `RequestValidationError → VALIDATION_ERROR (400)`, `KeyError/LookupError → NOT_FOUND (404)`, generic `Exception → INTERNAL_ERROR (500)` with the traceback only in the JSON log, never the response body.

Confirm `POST /v1/demo/run/{id}` is still <100ms (`asyncio.create_task` path — no regression). Confirm SQLite is in WAL mode by querying `PRAGMA journal_mode` from a one-off `uv run python` snippet against the running engine; expect `wal`. Confirm the secret redacting filter is wired by emitting a synthetic log record with `extra={"GATEWAY_ADAPTER_SECRET": "leak-me"}` and grepping the log output for `leak-me` (expect zero hits).

Run the three dress-rehearsal end-to-end checks from integration §6 (good full path, injection full path, approval full path) and fix anything that fails. Paste the curl outputs into the PR description and request review.

**Acceptance.** All three dress-rehearsal checks pass. Demo endpoint <100ms. Logs are JSON, secret-clean. PR approved + squash-merged.

**Verification.**
```bash
time curl -s -XPOST localhost:8000/v1/demo/run/good -o /dev/null
curl -s localhost:8000/v1/nope-does-not-exist | jq -e '.error.code=="NOT_FOUND"'
grep -c 'leak-me' /tmp/agentsheriff.log  # → 0
```

**Exit criteria for Run 5.**
- Dress rehearsal green.
- Logs JSON-clean and secret-redacted.
- Demo endpoint reliably <100ms.
- PR approved and squash-merged into `main`.

---

## Integration checkpoint

The following three commands are the final acceptance check, lifted from `specs/integration-and-handoffs.md` §6. Run them against the merged `main` build with backend on `:8000`.

```bash
# 1. Good scenario — allow with zero risk
curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' \
  -d @specs/fixtures/good.json \
  | jq -e '.decision=="allow" and .risk==0'

# 2. Injection scenario — deny with risk>=85, correct policy, agent jailed
INJ_AGENT=$(curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' \
  -d @specs/fixtures/injection.json | jq -r '.agent_id')
curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' \
  -d @specs/fixtures/injection.json \
  | jq -e '.decision=="deny" and .risk>=85 and .policy=="no-external-pii"'
curl -s localhost:8000/v1/agents | jq -e --arg a "$INJ_AGENT" '.[] | select(.id==$a) | .state=="jailed"'

# 3. Approval scenario — backgrounded call blocks, operator approves, original resolves to allow
( curl -s localhost:8000/v1/tool-call -H 'content-type: application/json' \
    -d @specs/fixtures/approval.json > /tmp/approval.out ) &
sleep 1
APP_ID=$(curl -s 'localhost:8000/v1/approvals?state=pending' | jq -r '.[0].id')
curl -s -XPOST localhost:8000/v1/approvals/$APP_ID -H 'content-type: application/json' \
  -d '{"action":"approved"}'
wait
jq -e '.decision=="allow"' /tmp/approval.out
```

All three `jq -e` assertions must exit 0. When they do, Person 1's deliverable is done.
