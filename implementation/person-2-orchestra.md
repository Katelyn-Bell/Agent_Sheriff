# Person 2 — Policy Intelligence, Threat Signals, and Demo Simulator (Orchestra Run File)

**Owner:** Person 2
**Working directory:** `/Users/bernardorodrigues/Documents/Code/Agent_Sheriff/backend`
**Branch:** `person-2/policy-intelligence`
**Spec:** [`../specs/person-2-threats-simulator.md`](../specs/person-2-threats-simulator.md)
**Shared context:** [`../specs/_shared-context.md`](../specs/_shared-context.md)
**Integration contract:** [`../specs/integration-and-handoffs.md`](../specs/integration-and-handoffs.md)

## How to use this file

Each Run ships a stable helper surface that other people depend on. Push after each Run so Person 1 and Person 3 can wire to your results without waiting for the entire branch.

## Mission

Person 2 owns the intelligence layer:

- heuristic threat signals
- LLM judge helper
- starter policy generation
- replay evaluation helpers
- Deputy Dusty and the scenario fixtures

---

## Run 1 — Public interfaces and heuristic core

**Purpose.** Publish the stable imports and deterministic signal logic that Person 1 can wire immediately.

### Agent 1A — Public exports and structured result types

Implement `threats/__init__.py` and define:

- `ThreatSignal`
- `ThreatReport`
- `JudgeDecision`
- `JudgeResult`
- `PolicyGenerationResult`
- `EvalComparisonResult`

Export:

- `detect_threats`
- `judge_tool_call`
- `generate_starter_policy`
- `compare_replayed_decision`

**Acceptance**

- all exports import cleanly from `agentsheriff.threats`

### Agent 1B — Deterministic detector

Implement `detector.py` with the frozen signal taxonomy:

- prompt injection
- external recipient
- sensitive attachment
- sensitive path
- bulk exfiltration pattern
- destructive shell
- git history rewrite
- credential-like material
- untrusted URL

Return `ThreatReport` with `signals`, `aggregate_score`, `summary`, and `recommended_floor`.

**Acceptance**

- detector never raises on malformed input
- tests cover low-risk and high-risk cases

---

## Run 2 — LLM judge helper

**Purpose.** Add the prompted judge path that only runs after static rules delegate to it.

### Agent 2A — Judge helper with prompt caching and fallback

Implement `classifier.py` as the judge helper. It should:

- accept policy version, normalized request, and threat report
- return `allow`, `deny`, or `require_approval`
- produce both technical rationale and user explanation
- short-circuit to a safe deterministic fallback when the LLM path is disabled

**Acceptance**

- LLM-disabled mode returns instantly
- mocked LLM tests cover allow, deny, and approval outcomes

---

## Run 3 — Starter policy generation

**Purpose.** Add the first-run policy bootstrap that makes the product general-purpose.

### Agent 3A — Intent-to-policy generator

Implement `generator.py` to accept:

- free-text user intent
- tool manifest
- optional domain hint

Return:

- `intent_summary`
- starter `judge_prompt`
- starter `static_rules`
- generation notes

Generated rules should be conservative and always include a judge fallback.

**Acceptance**

- generation tests pass for finance, inbox, repo-maintenance, and research-style inputs

---

## Run 4 — Replay evaluation helpers

**Purpose.** Support policy regression testing on historical ledger entries.

### Agent 4A — Replay comparison logic

Implement `evaluator.py` so it compares original vs replayed outcomes and returns:

- agreement boolean
- replay reason
- disagreement category

Supported categories:

- `more_permissive`
- `more_restrictive`
- `reason_changed`
- `approval_vs_direct`
- `error`

**Acceptance**

- evaluator tests cover agreement and all disagreement categories

---

## Run 5 — Deputy Dusty and scenario fixtures

**Purpose.** Keep the demo path strong while making it a verification asset instead of the full product definition.

### Agent 5A — Scenario JSON and Dusty CLI

Implement or refresh:

- `demo/scenarios/good.json`
- `demo/scenarios/injection.json`
- `demo/scenarios/approval.json`
- `demo/deputy_dusty.py`

Requirements:

- all scenarios use canonical `ToolCallRequest` shape
- `injection.json` may keep top-level `injection_payload`
- `good` demonstrates clean allow behavior
- `injection` demonstrates a deny with high-risk reasoning
- `approval` demonstrates human-in-the-loop resolution

Dusty should support:

- `--scenario good|injection|approval`
- `--all`
- configurable base URL

**Acceptance**

- Dusty can drive all three scenarios against the live backend
- rules-only mode still preserves the expected decision buckets

---

## Cross-team handoffs

- **To Person 1:** helpers for detect, judge, generate, and replay comparison
- **To Person 3:** user explanations and disagreement categories
- **To Person 4:** scenario compatibility and tool-risk assumptions

---

## Final acceptance

Person 2 is done when:

1. heuristic signals are stable and deterministic
2. the judge helper works with and without the LLM path
3. starter policy generation produces editable drafts
4. replay evaluation helpers support eval UI and backend persistence
5. Deputy Dusty still drives the three canonical scenarios
