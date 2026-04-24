# Person 2 — Threats + Simulator (Orchestra Run File)

**Owner:** Person 2
**Working directory:** `/Users/ianrowe/git/Agent_Sheriff/backend`
**Branch:** `person-2/threats-simulator`

## How to use this file
Each Run is a checkpoint. Within a Run, the listed agent prompts may execute in parallel — they touch disjoint files and share no in-flight state. Do not start Run N+1 until Run N's acceptance check passes and the branch is pushed (P1, P3, and P4 import P2's surface, so each Run has downstream consumers waiting). Every prompt is intent-driven: it tells you what to ship and why it matters, cites the binding spec sections, and trusts you to choose the implementation. Always read the cited spec passages before opening an editor; they contain locked field names, regexes, and aggregate formulas that integration tests assert against.

## Assumptions
- Python 3.11, `uv` package manager, `pytest` + `pytest-asyncio` available.
- `ANTHROPIC_API_KEY` is **optional** — every code path must work offline (`USE_LLM_CLASSIFIER=0` is the demo-day kill switch).
- P1 has scaffolded `backend/pyproject.toml`, `models/dto.py` (with reconciled fields per integration spec §1), and an empty `gateway.py` by H2.
- P4 owns `adapters/__init__.py` (`DISPATCH`), `_seed.py`, and `demo/openclaw-config/tools.yaml`.
- The public import surface `from agentsheriff.threats import …` is **locked** at H2 — renaming any of `score / rationale / suggested_policy / user_explanation` breaks P1, P3, and P4 simultaneously.

---

## Run 1 — Types + empty detector (H0 → H2) — UNBLOCKS P1

**Purpose.** Ship the dataclasses and an empty-but-valid `detect_threats` + `classify_risk` so P1's gateway can import the symbols and start wiring orchestration. This is the team's tightest dependency edge — everything else for P2 happens after this is merged.
**Dependencies.** None.
**Parallel agents.** 1.

### Agent 1A — Dataclasses, flat import surface, and never-raising stubs

Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-2-threats-simulator.md` §1 and §1.5, plus `/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md` §1 (the row "ClassifierResult field names"). Your job is to publish the public surface of `agentsheriff.threats` so P1 can import against it within 90 minutes of the hackathon starting.

Author `backend/src/agentsheriff/threats/__init__.py` exporting exactly these symbols: `SignalKind`, `ThreatSignal`, `ThreatReport`, `ClassifierResult`, `detect_threats`, `classify_risk`. The `ClassifierResult` field names — `score: int`, `rationale: str`, `suggested_policy: str | None`, `user_explanation: str` — are **canonical and locked**; any rename is a cross-team contract break. Use frozen dataclasses with `to_dict()` helpers as the spec models them.

Then stub `detector.py` so `detect_threats(request)` returns `ThreatReport()` (empty signals, aggregate 0). Stub `classifier.py` so `classify_risk(request, report)` is `async`, never raises, and short-circuits to a rules-only result whenever `ANTHROPIC_API_KEY` is unset or `USE_LLM_CLASSIFIER` is `"0"`/`"false"`. The rules-only fallback should compose a `ClassifierResult` directly from the `ThreatReport` (score = `report.aggregate_score`, rationale and user_explanation derived from `report.summary` or signals). Both stubs must accept `ToolCallRequest` from `agentsheriff.models.dto` (P1's DTO) and tolerate missing fields.

Add a tiny smoke test (`backend/tests/test_detector.py::test_imports_and_empty_report`) that imports the public surface, calls `detect_threats` on a minimal request, asserts `ThreatReport` shape, and `await`s `classify_risk` with `ANTHROPIC_API_KEY` unset to confirm instant return.

**Acceptance.** `uv run python -c "from agentsheriff.threats import detect_threats, classify_risk, ThreatReport, ClassifierResult, ThreatSignal, SignalKind"` succeeds. The smoke test passes. P1 can pull this branch and import without error.
**Verification.** `cd backend && uv sync && uv run pytest tests/test_detector.py -v`. Push branch; ping P1.

---

## Run 2 — Rule-based detector (H2 → H6)

**Purpose.** Implement every signal kind with the locked aggregation formula, including the `EXFIL_COMBO` boost that pushes the injection scenario over the `≥ 85` demo threshold even with the LLM offline.
**Dependencies.** Run 1 merged.
**Parallel agents.** 1.

### Agent 2A — Full detector + 12 unit tests

Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-2-threats-simulator.md` §2 (full detector source + curated patterns) and §6 (test plan). Replace the Run 1 stub with a real rule-based detector.

Implement all eight signal kinds: `INJECTION_PHRASE`, `EXTERNAL_RECIPIENT`, `SENSITIVE_ATTACHMENT`, `BASE64_BLOB`, `SECRETS_PATH`, `SHELL_DESTRUCTIVE`, `GITHUB_FORCE_PUSH`, and the synthetic `EXFIL_COMBO` (severity 90, fired when an external recipient and a sensitive attachment co-occur). The aggregation formula is **locked**: `aggregate = min(100, top_severity + floor(0.2 * sum(other_severities)))`. Do not invent your own — P1's policy thresholds depend on it.

`SENSITIVE_FILE_RE` must include `invoice|employees|customers` so the approval scenario's `invoice_q1.pdf` triggers `SENSITIVE_ATTACHMENT` cleanly. Document this regex as the single source of truth and link to it from any P1/P4 cross-references. `INTERNAL_DOMAINS` must keep `accountant@example.com`'s domain (`example.com`) classified as internal — **do not change this**, the entire approval scenario depends on it routing through the `approval-on-attachment` rule rather than the external-recipient deny path.

Add a CLI debug harness: `python -m agentsheriff.threats.detector path/to/scenario.json` prints each step's `ThreatReport` as JSON so you can sanity-check scenario files before pushing. Author 12+ unit tests in `backend/tests/test_detector.py` covering: clean inbox read, external recipient alone, sensitive attachment alone, exfil combo, base64 blob, secrets path, destructive shell (`rm -rf /`), GitHub force-push, injection phrase in `source_content` only, the locked aggregate math at the boundary, the approval scenario falling in the 50–84 band, and a guarantee that `detect_threats` never raises on malformed input.

The function must remain pure-Python, complete in <5ms, and never raise — wrap any defensive parsing in `try/except` returning empty `ThreatReport()`.

**Acceptance.** `uv run python -m agentsheriff.threats.detector backend/src/agentsheriff/demo/scenarios/injection.json` (after Run 4) shows step 3 with `aggregate_score >= 85` and an `EXFIL_COMBO` signal. All 12+ tests green.
**Verification.** `uv run pytest backend/tests/test_detector.py -v`.

---

## Run 3 — Claude classifier with caching + degradation (H6 → H8)

**Purpose.** Layer Haiku scoring and Sonnet user-explanation on top of the rule-based detector with ephemeral prompt caching, a hard 3s wall-clock ceiling, and graceful degradation back to rules-only on any failure.
**Dependencies.** Run 2 merged.
**Parallel agents.** 1.

### Agent 3A — Haiku + Sonnet + graceful degradation + 8 offline tests

**Invoke the `claude-api` skill first** — it contains the prompt-caching patterns this code must follow (cache_control on stable system blocks, `AsyncAnthropic` setup, model id strings, retry semantics). Then read `/Users/ianrowe/git/Agent_Sheriff/specs/person-2-threats-simulator.md` §3.

Models are locked: `claude-haiku-4-5-20251001` for the structured risk score, `claude-sonnet-4-6` for the human-readable Wanted Poster explanation. The Haiku call returns strict JSON `{score: int 0-100, rationale: str, suggested_policy: str | null}` — parse defensively and fall back to rules on any JSON error. Sonnet only runs when the Haiku score (or `report.aggregate_score`, whichever is higher) is `≥ 51`; for low-risk allowed traffic we don't burn Sonnet tokens. The final `ClassifierResult.score` is `max(haiku_score, report.aggregate_score)` — rules can always escalate.

Use `cache_control: {"type": "ephemeral"}` on the static system prompts. The cache key must be stable across requests, so any per-request data (the request payload, the threat report) goes in the user message, never the system block. Lazy-initialise a single `AsyncAnthropic` client behind an `asyncio.Lock` so we don't construct it until the first LLM-eligible request. Wrap each model call in `asyncio.wait_for(..., timeout=3.0)`; on `TimeoutError`, any exception, or a parse failure, log at WARNING and return `_rules_only(report)`. The classifier must **never** raise — P1 calls it unconditionally.

Short-circuit instantly (no client construction, no network) when `ANTHROPIC_API_KEY` is unset OR `USE_LLM_CLASSIFIER` is `"0"` / `"false"`. This is the offline demo path and it must return in microseconds.

Write 8+ tests in `backend/tests/test_classifier.py` using `unittest.mock.AsyncMock` for the Anthropic client: rules-only fast path, Haiku-only on medium risk, Haiku+Sonnet on high risk, Haiku timeout falls back to rules, malformed JSON falls back to rules, `USE_LLM_CLASSIFIER=0` short-circuits without instantiating the client, score escalation when rules outrank Haiku, and `user_explanation` populated from Sonnet when present.

**Acceptance.** With `ANTHROPIC_API_KEY` unset, `await classify_risk(req, report)` returns in <10ms. With the LLM mocked, all 8 tests green.
**Verification.** `uv run pytest backend/tests/test_classifier.py -v`.

---

## Run 4 — Scenario JSON + Deputy Dusty CLI (H8 → H12)

**Purpose.** Author the three canonical scenario files (the authoritative payloads every other person reads) and ship the colorised Deputy Dusty CLI that drives them, including the `--all` jailbreak-release ritual that lets the demo run back-to-back without manual intervention.
**Dependencies.** Run 3 merged.
**Parallel agents.** 2 (disjoint files — JSON vs. CLI — safe to run concurrently).

### Agent 4A — Scenario JSON files (good / injection / approval)

Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-2-threats-simulator.md` §5 and `/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md` §1 (the row "`injection_payload` string"). Author three files under `backend/src/agentsheriff/demo/scenarios/`: `good.json`, `injection.json`, `approval.json`.

Each file follows the shape `{agent_id, label, scenario, steps:[{delay_ms, tool, args, context}]}` from `_shared-context.md`. Use realistic prose in `context.source_prompt` and `context.source_content` — the demo's narrative believability comes from these strings.

`injection.json` MUST carry a top-level `"injection_payload"` string (peer to `agent_id`/`steps`). This is the **single source of truth** P4's `_seed.py` reads to keep the seeded `mock-fs/` web page in lockstep with the scenario; it is the contract from integration spec §1, fix #5. The payload is canonical (~300 chars), contains literally `Ignore previous instructions`, the recipient `outlaw@badmail.com`, and the filename `contacts.csv`. The same string must appear verbatim inside step 0's `source_content` (HTML-comment camouflage like `<!-- … -->` is fine and makes the demo more convincing). Step 3 is the `gmail.send_email` exfil that must trip `EXFIL_COMBO` — confirm with the Run 2 CLI harness that it scores `≥ 85`.

`approval.json` uses `accountant@example.com` (internal) as the recipient and `/home/user/invoices/invoice_q1.pdf` as the attachment so the detector lands in the 50–84 band and the policy router sends it to `approval-on-attachment` rather than denying or auto-allowing.

`good.json` is two clean steps: `gmail.read_inbox` then `calendar.create_event` (the `calendar` adapter is owned by P4 per integration spec §1 fix #8).

**Acceptance.** `uv run python -m agentsheriff.threats.detector backend/src/agentsheriff/demo/scenarios/injection.json` prints step-3 score `≥ 85` with an `EXFIL_COMBO` signal. The injection payload string appears identically as a top-level key and inside step-0 `source_content`.
**Verification.** Diff scenario JSONs against P4's `_seed.py` consumer site once P4's branch is available; flag mismatches in Run 5.

### Agent 4B — Deputy Dusty CLI

Read `/Users/ianrowe/git/Agent_Sheriff/specs/person-2-threats-simulator.md` §4 and `/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md` §1 (rows on `AGENTSHERIFF_BASE_URL` and the demo trigger endpoint). Build `backend/src/agentsheriff/demo/deputy_dusty.py` as the live demo's heartbeat.

Entry point: `python -m agentsheriff.demo.deputy_dusty --scenario {good|injection|approval}` plus `--all` to run all three sequentially. Flags: `--base-url` (defaults to env `AGENTSHERIFF_BASE_URL`, then `http://localhost:8000`) and `--delay-multiplier` (float, scales every `delay_ms`). Use `httpx.AsyncClient` with a **130s timeout** — strictly greater than the gateway's 120s approval window so the approval scenario's blocking HTTP call doesn't time out before the Sheriff clicks.

Render output with ANSI colours: green for `ALLOW`, red for `DENY`, amber/yellow for `APPROVAL_REQUIRED`. Show tool, decision, risk score, and `user_explanation` (if present). Exit codes: `0` clean run, `2` if any unexpected `DENY`, `3` if a tool call errors transport-side.

**Critical for `--all`:** the injection scenario will jail `deputy-dusty` mid-run. Without intervention, the approval scenario then fails because the agent is blocked. Before each scenario in the `--all` loop, POST `/v1/agents/deputy-dusty/release` to clear jail state; tolerate `404` (P1 may not have wired the endpoint yet on first integration). Insert a 2s pause between scenarios so the dashboard's animations resolve cleanly.

Write an integration test that spins a fake FastAPI echo server and runs each scenario against it, asserting the CLI emits the expected colour/decision pattern and exit code.

**Acceptance.** `python -m agentsheriff.demo.deputy_dusty --all` against P1's gateway produces a 2-allow / 2-allow + 1-deny / 1-allow + 1-approval-required-then-allow row pattern, with the injection scenario not blocking the approval scenario.
**Verification.** `uv run pytest backend/tests/test_deputy_dusty.py -v` against the fake server.

---

## Run 5 — Demo hardening (H12 → H16)

**Purpose.** Prove the offline rules-only path keeps decision buckets stable, document the prompt-cache warmup ritual for demo day, and reconcile any drift between P2's scenario JSONs and P4's seed/`tools.yaml`.
**Dependencies.** Run 4 merged AND P4's adapter integration available on `main`.
**Parallel agents.** 1.

### Agent 5A — Offline verification + P4 alignment + cache warmup docs

Read `/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md` §4 (the H14–H18 polish row for P2) and §6 (the offline-proof dress rehearsal step). Your job is to make the demo bulletproof regardless of network or API-key state.

First, run the offline proof: `unset ANTHROPIC_API_KEY; USE_LLM_CLASSIFIER=0 uv run python -m agentsheriff.demo.deputy_dusty --all`. Confirm decision buckets hold: `good` ends with two ALLOW rows; `injection` step 3 is DENY with `risk_score ≥ 85`; `approval` step 2 is `APPROVAL_REQUIRED` in the 50–84 band, then ALLOW after the Sheriff approve POST. Numeric scores will drift between LLM-on and LLM-off — that's expected — but bucket boundaries must be identical. If any bucket flips, write a regression test that pins the rules-only outcome (in `test_detector.py`) before tuning thresholds; never silently change the aggregate formula.

Second, document the prompt-cache warmup ritual in a short README block alongside the CLI (or in `demo/README.md` if P4 has bootstrapped it). The ritual: run `--all` twice pre-demo against the live gateway, watch Haiku p95 latency in logs, and if p95 exceeds 3s flip `USE_LLM_CLASSIFIER=0` for the live run. Cache warmup is what keeps Haiku under the 3s `wait_for` ceiling on a cold venue network.

Third, reconcile with P4. Diff the three scenario JSONs against `demo/openclaw-config/tools.yaml` (tool names) and against P4's `_seed.py` output (the seeded `mock-fs/` page that contains `injection_payload`, the seeded `/home/user/invoices/invoice_q1.pdf`, and the seeded `contacts.csv`). If anything is misaligned — a tool name typo, a path mismatch, a payload-string drift — open a PR comment on P4's branch and let them fix on their side. Do **not** silently mutate P2's scenarios to paper over P4 bugs; the scenario files are the contract per integration spec §1.

**Acceptance.** Both `USE_LLM_CLASSIFIER=1` and `USE_LLM_CLASSIFIER=0` runs of `--all` produce identical decision buckets (allow/allow ; allow/allow/deny ; allow/approval→allow). The prompt-cache warmup paragraph is committed. Any P4 misalignment has an open PR comment.
**Verification.** Both Dusty `--all` invocations exit `0`; the dashboard ledger (P3) shows the canonical 2/3/2 row pattern under both env settings.

---

## Integration checkpoint

With P1 gateway running on :8000 and P4's `_seed.py` having populated `mock-fs/`:

```bash
cd /Users/ianrowe/git/Agent_Sheriff/backend
uv run pytest tests -v                                   # all green (detector + classifier + dusty)
uv run python -m agentsheriff.demo.deputy_dusty --all    # LLM path
USE_LLM_CLASSIFIER=0 uv run python -m agentsheriff.demo.deputy_dusty --all   # rules-only path
```

Both runs must produce: `good` = 2 ALLOW; `injection` = 2 ALLOW + 1 DENY (`risk_score ≥ 85`) + agent JAILED + released by `--all` between scenarios; `approval` = 1 ALLOW + 1 APPROVAL_REQUIRED → APPROVE → completes ALLOW. **A bucket flip between LLM-on and LLM-off is a broken fallback path** — escalate immediately; do not paper over by tuning thresholds the morning of the demo.
