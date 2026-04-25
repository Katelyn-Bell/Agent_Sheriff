# Person 3 — Dashboard UI Spec

> Owner: Person 3
> Primary directory: `frontend/`
> Read [`specs/_shared-context.md`](./_shared-context.md) and [`specs/integration-and-handoffs.md`](./integration-and-handoffs.md) first.

## Mission

Build the dashboard for a general-purpose local tool-call policy gateway, not just a one-off hackathon visualization.

The UI must do two jobs at the same time:

1. work as a real operator console for policies, approvals, audit, and evals
2. preserve the Old-West character and the high-drama demo moments that make AgentSheriff memorable

## Product posture

Keep the Old-West shell, typography, palette, and motion language.

Do **not** keep the old product limitation where the app is only about three scripted scenes.

The new UI should feel like:

- a sheriff's office for agent governance
- a policy workshop
- a live audit and eval console

## Primary surfaces

### 1. Town Overview

This remains the landing page.

Show:

- live ticker of recent audit entries
- KPI cards for allowed, denied, awaiting approval, and active policy version
- quick actions to run demo scenarios
- a summary panel for the currently published policy
- latest eval run status

### 2. Town Laws

This becomes the core product page, not a side editor.

Support:

- create a new draft policy
- view current published policy
- edit `intent_summary`
- edit `judge_prompt`
- inspect and reorder static rules
- publish a draft version

### 3. First Ride

Add a first-run setup flow for generating a starter policy from user intent.

This should collect:

- policy name
- what the user uses the agent for
- optional domain hint

Then call `POST /v1/policies/generate` and open the resulting draft in Town Laws.

### 4. Sheriff's Ledger

Upgrade the ledger page into a real audit workbench.

Support:

- filters by decision, agent, policy version, and time
- rich row expansion
- display of heuristic summary, matched rule, judge usage, approval id, and execution summary

### 5. Badge Approval

Keep this page and keep it prominent.

It should show:

- pending approvals
- countdown
- action buttons for approve, deny, redact
- reason, agent, tool, and policy version context

### 6. Deputies

This page now represents agent runtimes and their recent activity rather than only demo characters.

Show:

- agent state
- request counts
- blocked counts
- active policy version if available
- recent decision history

### 7. Wanted Board

Keep this page because it is product-significant, not just theatrical.

It now highlights the most important denies:

- dangerous blocked actions
- jailbreak or exfiltration attempts
- repeated high-risk patterns

### 8. Trial Records

Add an eval-focused page for replay runs.

Show:

- eval run list
- status and progress
- agreement rates
- row-level disagreement inspection

## Core routes

Minimum route set:

```text
/
/first-ride
/laws
/ledger
/approvals
/deputies
/wanted
/evals
/evals/[id]
```

## Data model expectations

Person 1 owns backend DTOs. You mirror them exactly in `frontend/src/lib/types.ts`.

At minimum the frontend must support:

- `ToolCallResponse`
- `AuditEntryDTO`
- `ApprovalDTO`
- `PolicyVersionDTO`
- `StaticRuleDTO`
- `EvalRunDTO`
- `EvalResultDTO`
- stream frame union

Do not invent parallel frontend-only decision names.

## New UI capabilities required by the merge

### Policy versioning

The UI must clearly distinguish:

- draft version
- published version
- archived version

The user should never be confused about which version is live.

### Policy generation

Support a guided create flow backed by `POST /v1/policies/generate`.

The generated output should open into an editable draft state, not silently publish.

### Eval workflows

Users must be able to:

- launch an eval run
- monitor progress
- inspect disagreements
- compare original vs replayed decisions

### Rich audit detail

For each audit row, display:

- tool
- args snapshot
- context snapshot
- matched rule id
- whether the judge was used
- judge rationale
- policy version used
- approval metadata
- execution summary

## Real-time behavior

Use `WS /v1/stream` for live updates.

Support these frame types:

- `audit`
- `approval`
- `agent_state`
- `policy_published`
- `eval_progress`
- `heartbeat`

If the socket drops, reconnect automatically and rehydrate via REST.

## Old-West design rules

Keep:

- parchment background
- brass accents
- Wanted red for blocks
- approval amber for human review
- Rye headings and Inter body

Do not let the product expansion drift into generic SaaS styling.

## Required components

### `PolicyWorkbench`

Owns draft editing for:

- intent summary
- judge prompt
- static rules list

### `StarterPolicyWizard`

Collects initial user intent and calls policy generation.

### `EvalRunTable`

Lists eval runs with status and agreement metrics.

### `EvalDisagreementPanel`

Shows original decision, replayed decision, replay reason, and disagreement category.

### `WantedPoster`

Still used for major deny moments and must accept data from real audit rows, not just scenario fixtures.

### `ApprovalCard`

Still supports `approve`, `deny`, and `redact`.

## Page-specific expectations

### Town Overview

Must include:

- `Run Good`
- `Run Injection`
- `Run Approval`

These buttons remain because demoability is still important.

### Town Laws

Must include:

- policy version selector
- draft editor
- publish button
- generated-notes panel from starter policy generation

### Sheriff's Ledger

Must feel more like CrabTrap's audit trail quality, but rendered in AgentSheriff's visual system.

### Trial Records

Must allow drilling from run summary into row-level eval results.

## Integration contracts

### With Person 1

You depend on:

- backend DTOs
- policy endpoints
- eval endpoints
- stream frame union

### With Person 2

You depend on:

- user explanations
- replay disagreement categories

### With Person 4

You depend only on adapter result summaries and demo scenario hooks, not adapter internals.

## Testing and verification

Minimum UI verification cases:

1. Generate a starter policy draft from free-text intent.
2. Edit and publish a policy version.
3. View a live allow decision on Town Overview and in the Ledger.
4. View a deny on the Wanted Board with real audit-driven data.
5. Resolve a pending approval from the Badge Approval page.
6. Start an eval run and watch progress without a full page refresh.
7. Inspect a disagreement on the Trial Records page.

## Acceptance criteria

You are done when:

- the UI supports the generalized policy workflow, not just demo playback
- Town Laws is a real policy workbench
- eval creation and inspection are implemented
- audit detail is rich enough to explain decisions
- the Old-West design language remains intact
- `good`, `injection`, and `approval` still look strong in the live demo

## Explicit non-goals

Do not take ownership of:

- backend rule evaluation
- policy generation logic quality
- adapter behavior
- transparent HTTP proxy UX
