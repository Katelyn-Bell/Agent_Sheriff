# Person 2 — Policy Intelligence, Threat Signals, and Demo Simulator

> Owner: Person 2
> Primary directories: `backend/src/agentsheriff/threats/`, `backend/src/agentsheriff/demo/`, `backend/tests/`
> Read [`specs/_shared-context.md`](./_shared-context.md) and [`specs/integration-and-handoffs.md`](./integration-and-handoffs.md) first.

## Mission

Own the intelligence layer that makes the gateway useful beyond static allowlists.

Your scope now includes:

- heuristic threat and risk signals
- the LLM judge helper used by Person 1
- starter policy generation from user intent
- replay evaluation helpers
- Deputy Dusty and the scenario fixtures used for smoke tests and demos

You are no longer just the "threats person". You own the logic that helps the system:

- interpret risk
- draft starter restrictions
- explain decisions
- compare current and replayed behavior

## Outputs you own

```text
backend/src/agentsheriff/threats/
├── __init__.py
├── detector.py
├── classifier.py
├── generator.py
└── evaluator.py

backend/src/agentsheriff/demo/
├── __init__.py
├── deputy_dusty.py
└── scenarios/
    ├── good.json
    ├── injection.json
    └── approval.json

backend/tests/
├── test_detector.py
├── test_classifier.py
├── test_generator.py
└── test_evaluator.py
```

## 1. Public interfaces

Person 1 consumes your package as a stable API. Export these symbols from `agentsheriff.threats`:

- `ThreatSignal`
- `ThreatReport`
- `JudgeDecision`
- `JudgeResult`
- `PolicyGenerationResult`
- `EvalComparisonResult`
- `detect_threats`
- `judge_tool_call`
- `generate_starter_policy`
- `compare_replayed_decision`

## 2. Threat and heuristic detection

Implement `detector.py` as a fast, deterministic pass over the normalized tool call.

### Minimum signal taxonomy

- `prompt_injection`
- `external_recipient`
- `sensitive_attachment`
- `sensitive_path`
- `bulk_exfiltration_pattern`
- `destructive_shell`
- `git_history_rewrite`
- `credential_like_material`
- `untrusted_url`

### Output shape

`ThreatReport` should include:

- `signals`
- `aggregate_score`
- `summary`
- `recommended_floor`

### Design constraints

- synchronous and fast
- no network calls
- never raise for malformed tool args
- useful both for live decisions and replay evals

## 3. LLM judge helper

Implement `classifier.py` as the judge helper, even though the module name stays legacy-friendly.

### Job of the judge helper

Given:

- active policy version
- normalized tool call
- heuristic report

Return:

- decision: `allow`, `deny`, or `require_approval`
- rationale for technical inspection
- user explanation for UI surfaces
- optional severity recommendation

### Guardrails

- rules-first architecture means this should only run after `delegate_to_judge` or no rule match
- prompt caching is mandatory
- when the LLM path is disabled or unavailable, return a deterministic safe fallback
- the helper must not own persistence or HTTP behavior

### Fallback behavior

When `USE_LLM_CLASSIFIER=0` or no API key is available:

- use heuristic report + conservative heuristics to settle borderline cases
- do not crash the gateway
- preserve the demo scenarios

## 4. Starter policy generation

Implement `generator.py`.

This is the CrabTrap-inspired addition that turns the project into a general product.

### Input

- free-text user intent
- tool manifest or tool catalog
- optional domain hint, such as finance or support

### Output

- `intent_summary`
- starter `judge_prompt`
- starter `static_rules`
- generation notes

### Rules for generated output

- generated rules should be conservative, not permissive
- include at least one rule for external sends, one for sensitive material, and one judge-delegation fallback
- do not auto-publish
- treat the output as draft material for user editing

### Examples the generator should handle

- inbox triage assistant
- finance operations assistant
- repo maintenance assistant
- browser research assistant

## 5. Replay evaluation helper

Implement `evaluator.py`.

This helper compares:

- original audit decision and context
- replayed policy decision

It should produce:

- agreement boolean
- replay reason
- high-level disagreement category

Suggested disagreement categories:

- `more_permissive`
- `more_restrictive`
- `reason_changed`
- `approval_vs_direct`
- `error`

## 6. Deputy Dusty and scenarios

Keep Deputy Dusty and the three scenario JSON files, but treat them as:

- smoke tests
- demo fixtures
- regression coverage for the generalized architecture

They are no longer the whole product story.

### Scenario requirements

- `good` must demonstrate a normal allowed workflow
- `injection` must still end in a deny with high-risk reasoning
- `approval` must still end in a human-approved outcome

### Fixture discipline

- scenario payloads must match the canonical `ToolCallRequest` shape
- the scenario fixtures must remain stable enough for backend and UI tests
- `injection.json` may keep a top-level `injection_payload` field for cross-team reuse

## 7. Integration contracts

### With Person 1

Person 1 calls:

- `detect_threats(request)`
- `judge_tool_call(policy_version, request, threat_report)`
- `generate_starter_policy(user_intent, tool_manifest, domain_hint=None)`
- `compare_replayed_decision(audit_entry, replay_outcome)`

These helpers must:

- be importable without side effects beyond config setup
- return structured results, not raw strings
- never require HTTP context

### With Person 3

Person 3 depends on:

- `user_explanation`
- stable decision labels
- disagreement categorization for eval UI

### With Person 4

Person 4 depends on:

- scenario fixtures
- assumptions about sensitive tools and risky patterns

## 8. Tests

### `test_detector.py`

Cover:

- low-risk normal email/calendar flow
- exfiltration pattern with external recipient plus sensitive attachment
- shell destructive command
- force push pattern

### `test_classifier.py`

Cover:

- judge allow case
- judge deny case
- judge approval case
- rules-only fallback when LLM is disabled

### `test_generator.py`

Cover:

- starter rules generated from a finance assistant prompt
- generated prompt is non-empty
- generated rules include a default judge delegation path

### `test_evaluator.py`

Cover:

- agreement
- more permissive replay
- more restrictive replay
- approval-vs-direct disagreement

## 9. Acceptance criteria

You are done when:

- heuristic detection produces stable, replayable signals
- the judge helper can return allow, deny, or require-approval outcomes
- starter policy generation works from user intent plus tool manifest
- replay comparison results are structured enough for UI display
- Deputy Dusty still drives `good`, `injection`, and `approval`
- all helper logic works with the LLM disabled

## 10. Explicit non-goals

Do not take ownership of:

- persistence and REST endpoints
- frontend UX
- adapter execution
- any transparent HTTP proxy interception work
