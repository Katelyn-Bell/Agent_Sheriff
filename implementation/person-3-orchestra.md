# Person 3 — Dashboard UI (Orchestra Run File)

**Owner:** Person 3
**Working directory:** /Users/ianrowe/git/Agent_Sheriff/frontend
**Branch:** person-3/dashboard-ui
**Spec:** /Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md
**Shared context:** /Users/ianrowe/git/Agent_Sheriff/specs/_shared-context.md
**Reconciliation (wins on conflict):** /Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md

## How to use this file

Each Run is a checkpoint. Within a Run, every Agent block is an independent prompt — paste it verbatim into a fresh Claude Code session opened to the working directory above. Agents inside a single Run touch disjoint files and can execute in parallel. Do not start a Run until the prior Run's acceptance gate is green and committed on the branch. Where this file and a per-person spec disagree, the integration-and-handoffs.md document wins; both are cited in every prompt so the agent can cross-check.

## Assumptions

- Node 20.x, pnpm or npm; Next.js 15 App Router with TypeScript strict mode (Next 14.2 / React 18 fallback documented at top of `package.json` as a comment if 15 has hackathon-blocking bugs).
- `NEXT_PUBLIC_USE_MOCKS=1` means Runs 1 and 2 require **no** running backend; the mock layer plays scripted REST + WS for `good`, `injection`, `approval`.
- Browser-side URLs MUST be `http://localhost:8000` and `ws://localhost:8000/v1/stream` — never the compose internal hostname `backend:8000`.
- `ApprovalState` is `"pending" | "approved" | "denied" | "redacted" | "timed_out"` (NOT `"expired"`). UI label for `timed_out` is "Timed Out".
- DTOs are locked per integration-and-handoffs.md §1; any drift means the frontend is wrong.
- `expires_at` arrives on `ApprovalDTO` from the backend — countdowns derive from `expires_at - now()`, never `ts + 120s`.
- WS is **server-push only**; the client does not send heartbeats/pings.
- Reconciled `AgentDTO` fields used by the UI: `id, label, state, created_at, last_seen_at, jailed_reason?, requests_today, blocked_today`.

---

## Run 1 — Scaffold + theme + mock layer (H0 → H4)

**Purpose.** Stand up the parchment-themed Next.js shell, the typed API/WS/store/mocks plumbing, and prove the dashboard boots end-to-end against the mock layer so Person 3 is unblocked while P1/P2/P4 are still landing stubs.
**Dependencies.** None (frontend works fully offline via mocks at this phase).
**Parallel agents.** 1.

### Agent 1A — Next.js scaffold, theme, types, api, ws, store, mocks

You are scaffolding the AgentSheriff frontend. Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Branch: `person-3/dashboard-ui`. Read **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** in full and **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §1, §3, §6 — those reconciliations override the per-person spec when they disagree.

Run `npx create-next-app@15 frontend --typescript --eslint --tailwind --app --src-dir --import-alias "@/*"` (fall back to Next 14.2 / React 18 if 15 misbehaves; document the fallback at the top of `package.json`'s "comment" field). Install: `shadcn-ui` (button, card, badge, dialog, table, sheet, tabs, input, textarea, select, scroll-area, tooltip, sonner), `lucide-react`, `framer-motion`, `react-use-websocket`, `@tanstack/react-query`, `@tanstack/react-virtual`, `zustand`, `zod`, `@uiw/react-codemirror`, `@codemirror/lang-yaml`.

Configure `tailwind.config.ts` with the locked palette: parchment `#f3e9d2`, brown `#3b2a1a`, brass `#b8864b`, wanted-red `#a4161a`, allowed-green `#2d6a4f`, approval-amber `#d68c1e`. Add keyframes `stamp-in` (scale 2.4→1, rotate -22deg→-3deg, opacity 0→1, ~280ms spring), `ticker-in` (translateY(-8px) + fade), `pulse-amber`. Wire **Rye** for `font-display` and **Inter** for `font-sans` via `next/font/google`. `globals.css`: SVG-noise parchment grain background utility `.paper`, `.wanted-stamp` for the deny overlay, brass focus ring, `@media (prefers-reduced-motion: reduce)` overrides that turn slam-in into a fade and remove pulse.

Build `src/components/Sidebar.tsx` with 6 routes (Town `/`, Wanted `/wanted`, Approvals `/approvals`, Deputies `/deputies`, Ledger `/ledger`, Laws `/laws`) and a `ConnectionBanner.tsx` that surfaces "Disconnected — reconnecting…" amber banner only when WS has been down >3s.

`src/lib/types.ts`: mirror every reconciled DTO verbatim (AgentDTO, AuditEntryDTO, ApprovalDTO with `expires_at` + `created_at` + `agent_label`, ToolCallResponse with `user_explanation`, ApprovalState union with `redacted` and `timed_out`). Add zod schemas for runtime validation of WS frames.

`src/lib/api.ts`: typed fetch wrappers for `/health`, `/v1/tool-call`, `/v1/audit?limit&agent_id&decision`, `/v1/agents`, `/v1/agents/{id}/{jail|release|revoke}`, `/v1/approvals`, `/v1/approvals/{id}`, `/v1/policies`, `/v1/policies/templates`, `/v1/policies/apply-template`, `/v1/demo/run/{id}`. Reads `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`).

`src/lib/ws.ts`: `react-use-websocket` hook, server-push-only (no client heartbeat), exponential reconnect 1s→10s capped, on every OPEN refetch approvals + agents + audit through react-query and merge into the store (no duplicates). Honor `NEXT_PUBLIC_POLL_FALLBACK=1` per fix #11.

`src/lib/store.ts`: zustand with a 500-entry audit ring buffer, `Map<id, ApprovalDTO>`, `Map<id, AgentDTO>`, connection state, and a `slamInQueue` for new deny audits.

`src/app/providers.tsx`: react-query client + Toaster.

Mock layer behind `NEXT_PUBLIC_USE_MOCKS=1`: a fake WS + fake fetch that scripts all three demo scenarios end-to-end (timed pushes for `good`, `injection`, `approval`), validated against the same zod schemas the live path uses.

**Acceptance.** `NEXT_PUBLIC_USE_MOCKS=1 npm run dev` boots; `localhost:3000` shows parchment background, sidebar with 6 routes, mock-mode banner; `npm run typecheck` passes; mock scenarios fire on demand. **Verification:** open the app, click a `Run Good` test trigger, see two green ticker rows.

---

## Run 2 — Demo-critical screens (H4 → H10)

**Purpose.** Build the two screens judges stare at: Town Overview (KPIs + demo launcher + live ticker + agent mini-cards) and the two money moments — the WantedPoster slam-in for deny, and the Approval amber card with a real countdown derived from `expires_at`.
**Dependencies.** Run 1 merged.
**Parallel agents.** 2 (disjoint files).

### Agent 2A — Town Overview + Wanted Board + WantedPoster slam-in

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §3 (Town Overview), §6 (WantedPoster). Reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §2.2 (injection sequence), §6 (acceptance matrix).

Implement `src/app/page.tsx` (Town Overview). Top: 4 `KpiCard`s — Allowed today, Blocked today, Awaiting Sheriff, Average risk score — each driving a framer-motion count-up tween on numeric change so the judges see the number tick. Pull values from the zustand store (memoize the selectors). Below: a "Run demo" launcher with three buttons (`good`, `injection`, `approval`) that POST `/v1/demo/run/{scenario_id}` with loading+disabled state per button. Below: a live ticker showing the last 12 audit entries with `animate-ticker-in`, decision-tinted left border (allowed-green / wanted-red / approval-amber). Right rail: agent mini-cards summarizing agent state and `last_seen_at`.

Implement `src/components/WantedPoster.tsx` and `src/app/wanted/page.tsx`. `/wanted` shows a grid of all current/past Wanted entries (deny audit rows with `agent_label`, `tool`, `reason`, `user_explanation`, `risk_score`, `policy_id`). On the Town Overview, subscribe to the store's `slamInQueue` — every new audit with `decision=="deny"` pushes a full-screen `WantedPoster` overlay. Animation: framer-motion spring (stiffness 280, damping 14), scale 2.4→1, rotate -22deg→-3deg, opacity 0→1; auto-dismiss after 2.4s OR on click; `prefers-reduced-motion` → cross-fade only. Typography must be legible from **3 metres on a 1080p projector** — Rye headline ≥ 96px, body ≥ 28px, high contrast on parchment.

Wire the agent state badge: when an `agent_state` WS frame arrives with `state=="jailed"`, the matching agent mini-card flips to wanted-red with a "JAILED" badge within 3s of the deny.

**Acceptance.** With `NEXT_PUBLIC_USE_MOCKS=1`: clicking *Run Injection* produces, within 3s, (a) a red ticker row, (b) the slam-in overlay, (c) `Blocked today` KPI increments, (d) the agent mini-card shows JAILED. With `prefers-reduced-motion: reduce` set, slam-in becomes a fade. No console errors. **Verification:** Lighthouse perf ≥85 on `/` and `/wanted` is checked in Run 4 — for now, just confirm visual behavior.

### Agent 2B — Approvals queue + ApprovalCard + A/D/R hotkeys

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §5 (Approvals); reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §1 (`ApprovalState`, `expires_at`), §2.3 (approval sequence), §6 (acceptance).

Implement `src/app/approvals/page.tsx` with two stacked sections: **Pending** (live, ordered by `expires_at` ascending) and **Resolved (last 30 min)** (approved/denied/redacted/timed_out, fade-in tinted by outcome). Pull from zustand; hydrate from `GET /v1/approvals?state=pending` on mount and on every WS OPEN.

Implement `src/components/ApprovalCard.tsx`. Render `agent_label`, `tool`, args (pretty-printed JSON in a collapsible block), `reason`, `user_explanation`, `policy_id`, `risk_score` (color-coded), and a **live countdown** computed every 250ms as `Math.max(0, expires_at - Date.now())`, formatted `mm:ss`, turning red below 15s. Do **not** compute the countdown from `ts + 120s` — `expires_at` is authoritative.

Three buttons: Approve (allowed-green), Deny (wanted-red), Redact (approval-amber). All three POST `/v1/approvals/{id}` with `{action, scope: "once"}`. **Crucially: redact does NOT mutate args client-side** — the client trusts the server's redaction transform (integration-and-handoffs.md fix #12). Implement keyboard shortcuts A / D / R that respect input focus (no fire when a textarea/input has focus). Show a sonner toast on each action and update the card optimistically; reconcile when the WS `approval` frame with the new state arrives (idempotent).

Add an overlay variant: when a new `pending` ApprovalDTO arrives while the user is on `/`, render the card as a centered modal with `animate-pulse-amber`. Dismiss on resolve.

**Acceptance.** With `NEXT_PUBLIC_USE_MOCKS=1`: clicking *Run Approval* yields a pulsing amber ApprovalCard with countdown >110s; pressing `A` resolves it green, slides it to Resolved, and the underlying mock HTTP completes within 1s. `expires_at` runs out → card transitions to a `Timed Out` (gray) state, never `Expired`. No console errors.

---

## Run 3 — Secondary screens (H10 → H14)

**Purpose.** Ship Deputies, Ledger, and Laws. Three independent pages, three parallel agents, one per page.
**Dependencies.** Run 2 merged.
**Parallel agents.** 3.

### Agent 3A — Deputies table + agent sheet

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §4 (Deputies). Reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §1 (AgentDTO has `last_seen_at`, `created_at`, `jailed_reason`, `requests_today`, `blocked_today`).

Implement `src/app/deputies/page.tsx`. Use shadcn `Table` with sortable columns: badge sigil, `id`, `state` (active/jailed/revoked badge), `created_at`, `last_seen_at`, `requests_today`, `blocked_today`, `jailed_reason`. Pull from `GET /v1/agents` via react-query and merge live WS `agent_state` updates from the store. Sortable client-side. Empty state: old-west copy ("No deputies on the trail yet — fire up Dusty.").

Row click opens a shadcn `Sheet` from the right with: header (label + state badge + jailed_reason if present), an `AuditTimeline` component filtered to that `agent_id` (last 100 entries from store + REST hydrate), and three action buttons: **Jail**, **Release**, **Revoke**. Each action POSTs the matching `/v1/agents/{id}/{action}` endpoint, fires a sonner confirmation, and disables itself on in-flight. Disable Jail when state==jailed, Release when state!=jailed, etc.

**Acceptance.** Table renders ≥ 1 row from mocks; sort by `last_seen_at` works; opening the Sheet shows the deputy's filtered audit history; clicking Jail flips the badge live and emits a toast. No console errors. **Verification:** axe-core scan on `/deputies` is clean (re-checked in Run 4).

### Agent 3B — Sheriff's Ledger (virtualized)

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §8 (Ledger). Reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §1 (AuditEntryDTO has `agent_label`, `user_explanation`).

Implement `src/app/ledger/page.tsx` using `@tanstack/react-virtual` for a virtualized list of up to 500 rows. On mount call `GET /v1/audit?limit=500` and load into the store ring buffer (de-duplicate by `id`); subscribe to live WS `audit` frames and prepend without unmount churn.

Each row: timestamp, `agent_label`, `tool`, decision pill, `risk_score` (color tinted), short reason. Decision-tinted left border (green/red/amber). Filters above the list: agent (select from current agents), decision (allow/deny/approval_required), free-text (matches `tool`, `reason`, JSON-stringified `args`). Filters apply client-side.

Row click opens a shadcn `Sheet` showing the full DTO: `args` (JSON), `result` (JSON if present), `user_explanation`, `policy_id`, `approval_id` (linked to the approval if resolvable). Add a "Copy JSON" button that copies the whole DTO.

**Acceptance.** With 500 mock rows the page scrolls smoothly (60fps target) on a mid-tier laptop; live append works without scroll jump while the user is at the top; filters narrow the visible set instantly. No console errors.

### Agent 3C — Town Laws (policy editor)

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §11 (Laws / Policy editor). Reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §1 (policy endpoints).

Implement `src/app/laws/page.tsx` with `@uiw/react-codemirror` + `@codemirror/lang-yaml`. Hydrate the editor from `GET /v1/policies` (returns YAML text inside `{ yaml: "..." }`). Apply a parchment-themed CodeMirror skin (parchment background, brown text, brass cursor). Dynamic-import the editor (`next/dynamic` `ssr: false`) so it doesn't bloat first paint.

Buttons: **Save** (PUT `/v1/policies` with `{ yaml }`; on 422 surface the error envelope `{error:{code,message}}` both in a sonner toast and inline beneath the editor with the offending line if present), **Reset** (re-fetch GET, confirm dialog if dirty), **Apply Template**. The template picker lists names from `GET /v1/policies/templates`; selecting one opens a confirm dialog ("This will overwrite current policies"); confirm POSTs `/v1/policies/apply-template` with `{name}`.

Show an "unsaved changes" amber pill in the header while the editor is dirty. Add a right-rail panel summarizing active rules (parsed from current YAML — tolerate parse errors gracefully).

**Acceptance.** Round-trip works: edit → Save → success toast; deliberately break YAML → Save → 422 envelope renders inline + as toast; template picker swaps active YAML after confirm; reset clears the dirty flag. No console errors.

---

## Run 4 — Live backend integration + polish (H14 → H18)

**Purpose.** Cut the mock layer off, validate against the live backend per the integration acceptance matrix, hit the a11y / Lighthouse / projector bars, and prove reconnect resilience.
**Dependencies.** Run 3 merged. Person 1 (`/v1/tool-call`, `/v1/audit`, approvals queue, `/v1/demo/run/{id}`, `/health`), Person 2 (scenarios + classifier), and Person 4 (compose / adapters) merged to `main`.
**Parallel agents.** 1.

### Agent 4A — Cutover, a11y, Lighthouse, projector tuning

Working dir: `/Users/ianrowe/git/Agent_Sheriff/frontend`. Spec: **/Users/ianrowe/git/Agent_Sheriff/specs/person-3-dashboard-ui.md** §13 (polish). Reconciliation: **/Users/ianrowe/git/Agent_Sheriff/specs/integration-and-handoffs.md** §6 (acceptance matrix), §3 (env vars), §5 (contingencies).

Write `.env.local`:
```
NEXT_PUBLIC_USE_MOCKS=0
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/v1/stream
NEXT_PUBLIC_POLL_FALLBACK=0
```

Bring up backend (`cd ../backend && uv run uvicorn agentsheriff.main:app --port 8000`) and run all 3 demo scenarios via the Town Overview launcher buttons against the **live** backend. Validate the Run 2/3 acceptance criteria still pass against real data; log any DTO drift as a P1 bug, do not patch the frontend types unilaterally.

Verify the WS path: open devtools Network → WS frames; confirm only server→client frames (the client never sends anything). Kill the backend; confirm the `ConnectionBanner` flips amber after >3s, exponential reconnect attempts visibly back off (1s→2s→4s→8s→10s capped). Restart backend; on the OPEN event confirm approvals + agents + audit are refetched and merged into the store with no duplicates (check by id).

Run `axe-core` (via `@axe-core/react` in dev or the CLI) on all 6 routes; fix every violation (color contrast, missing labels, focus traps in Sheet/Dialog, button names). Run Lighthouse on `/`, `/wanted`, `/approvals`, `/ledger`; achieve **≥ 85** perf on each. Levers: `next/font` with `display: "swap"`, memoize `KpiCard` and ticker rows, dynamic-import CodeMirror (already done in 3C — verify), tree-shake lucide imports, add `loading="lazy"` where applicable.

Projector tuning at 1920×1080: confirm slam-in WantedPoster is readable from 3m (Rye headline rendered ≥ 96px), ApprovalCard countdown ≥ 64px and red below 15s. At 1280px viewport the sidebar collapses to icons; verify nothing clips. Honor `prefers-reduced-motion`: slam-in becomes fade, amber pulse becomes a static border.

Run a full 3-scenario cycle and confirm **zero console errors and zero unhandled promise rejections** across all 6 routes.

**Acceptance.** All three scenarios green per integration-and-handoffs.md §6; Lighthouse ≥85 on the 4 primary routes; axe-core clean; reconnect hydrates without duplicates; reduced-motion honored; 1080p projector legibility verified; console clean. Commit and open PR to `main`.

---

## Integration checkpoint

Person 3 is done when, against a live backend on a clean checkout:

- All three demo scenarios trigger the correct visual story end-to-end:
  - **good** → 2 green ticker rows + Allowed-today KPI +2;
  - **injection** → red ticker row + slam-in WantedPoster + JAILED badge on agent + Blocked-today KPI +1, all within 5s;
  - **approval** → amber ApprovalCard with `expires_at`-driven countdown → click Approve → card turns green and exits → green allow ledger row appears within 1s.
- WS reconnect after a backend kill rehydrates pending approvals + agents + last 500 audit rows with no duplicate keys.
- Console is clean across all 6 routes through a full 3-scenario cycle.
- Lighthouse ≥ 85 on `/`, `/wanted`, `/approvals`, `/ledger`.
- `prefers-reduced-motion` users get a fade in place of slam-in and a static border in place of the amber pulse.
- Every screen is legible at 3m on a 1080p projector; sidebar collapses cleanly at 1280px.
- All DTO field names match integration-and-handoffs.md §1 verbatim — `last_seen_at`, `expires_at`, `created_at`, `agent_label`, `user_explanation`, `ApprovalState ∈ {pending, approved, denied, redacted, timed_out}`.
