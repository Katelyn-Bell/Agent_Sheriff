# Person 3 — Dashboard UI (Orchestra Run File)

**Owner:** Person 3
**Working directory:** `/Users/bernardorodrigues/Documents/Code/Agent_Sheriff/frontend`
**Branch:** `person-3/dashboard-ui`
**Spec:** [`../specs/person-3-dashboard-ui.md`](../specs/person-3-dashboard-ui.md)
**Shared context:** [`../specs/_shared-context.md`](../specs/_shared-context.md)
**Integration contract:** [`../specs/integration-and-handoffs.md`](../specs/integration-and-handoffs.md)

## How to use this file

Treat each Run as a checkpoint with a usable product slice. Build against the real backend contracts first, and use mocks only as a temporary bootstrap path when backend endpoints are not ready yet.

## Mission

Person 3 turns AgentSheriff into a real operator console while preserving the Old-West identity.

You own:

- policy authoring UX
- approvals UX
- audit and eval UX
- live stream integration
- the demo-critical overview, wanted, and approval moments

---

## Run 1 — Shell, types, and live data plumbing

**Purpose.** Build the application frame and the typed data layer that every page depends on.

### Agent 1A — App shell, routes, and design system

Set up:

- Next.js shell
- sidebar navigation
- route placeholders for `/`, `/first-ride`, `/laws`, `/ledger`, `/approvals`, `/deputies`, `/wanted`, `/evals`
- Old-West theme tokens and typography

**Acceptance**

- app boots with all core routes
- theme matches the shared palette

### Agent 1B — API, types, store, and stream client

Implement:

- `frontend/src/lib/types.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/store.ts`
- `frontend/src/lib/ws.ts`

Mirror backend DTOs exactly and support stream frames:

- `audit`
- `approval`
- `agent_state`
- `policy_published`
- `eval_progress`
- `heartbeat`

**Acceptance**

- REST client types compile
- WebSocket reconnects and rehydrates via REST

---

## Run 2 — Policy workflows

**Purpose.** Make the UI useful for the new generalized product flow.

### Agent 2A — First Ride starter-policy flow

Build `/first-ride` with a guided flow for:

- policy name
- user intent
- optional domain hint

Call `POST /v1/policies/generate` and route the user into an editable draft.

**Acceptance**

- generated policy draft opens into Town Laws

### Agent 2B — Town Laws policy workbench

Build `/laws` as a real policy editor, not just a YAML text area.

Support:

- draft selection
- current published version summary
- intent summary editing
- judge prompt editing
- static rule inspection and reordering
- publish action

**Acceptance**

- can create, inspect, edit, and publish a draft policy version

---

## Run 3 — Live governance surfaces

**Purpose.** Ship the pages operators will use day to day and the pages judges will remember.

### Agent 3A — Town Overview and demo launcher

Build `/` with:

- recent audit ticker
- KPIs
- current policy summary
- latest eval status
- buttons to run `good`, `injection`, and `approval`

**Acceptance**

- overview reflects live backend data
- demo launcher hits backend endpoints cleanly

### Agent 3B — Badge Approval and Wanted Board

Build:

- `/approvals`
- `/wanted`

Keep:

- approval countdown
- approve / deny / redact actions
- Wanted poster slam-in for major denies

**Acceptance**

- approvals resolve from the UI
- deny events can drive the Wanted flow from real audit rows

### Agent 3C — Deputies and Sheriff's Ledger

Build:

- `/deputies`
- `/ledger`

Support:

- filters
- row expansion
- display of matched rule, judge usage, approval metadata, and execution summary

**Acceptance**

- operator can inspect who acted, what happened, why it happened, and which policy version was used

---

## Run 4 — Trial Records and polish

**Purpose.** Complete the replay-eval UX and polish the full app for demos and real use.

### Agent 4A — Eval run list and detail pages

Build:

- `/evals`
- `/evals/[id]`

Support:

- eval run list
- progress updates
- aggregate stats
- disagreement drill-down

**Acceptance**

- eval runs are visible live without refresh
- detail view explains original vs replayed decision clearly

### Agent 4B — Accessibility, reconnect resilience, and projector-readability pass

Polish:

- reconnect banners
- reduced-motion handling
- focus states
- large-format readability for Wanted and Approval surfaces

**Acceptance**

- no console errors during the three-scenario flow
- reconnect path rehydrates without duplicates
- main demo surfaces remain legible on a projector

---

## Cross-team handoffs

- **From Person 1:** DTOs, REST endpoints, and stream frames
- **From Person 2:** user explanations and eval disagreement categories
- **From Person 4:** tool metadata and demo trigger integration

---

## Final acceptance

Person 3 is done when:

1. the UI supports starter policy generation and policy version editing
2. audit, approvals, and evals all render from live backend data
3. the Wanted and Approval moments still land well in the demo
4. the dashboard feels like a real product console, not just a scene board
