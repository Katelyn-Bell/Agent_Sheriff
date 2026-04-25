# AgentSheriff — Specs

Spec set for **AgentSheriff**: a local tool-call policy gateway for AI agents. It evaluates actions with deterministic static rules first, a prompted LLM judge second, optional human approval where needed, and a replayable audit ledger behind an Old-West control surface.

## Read order

1. **[_shared-context.md](_shared-context.md)** — product definition, architecture, stack, locked repo layout, API contracts, and definition of done.
2. **[integration-and-handoffs.md](integration-and-handoffs.md)** — shared DTOs, endpoint contracts, stream frames, env vars, and ownership boundaries.
3. Per-person specs (pick your own):
   - **[person-1-backend-core.md](person-1-backend-core.md)** — FastAPI gateway, policy versions, rule engine, approvals, audit ledger, eval APIs, and streams. *(Round 1 — shipped)*
   - **[person-2-threats-simulator.md](person-2-threats-simulator.md)** — heuristics, judge helper, starter policy generation, replay evaluation helpers, Deputy Dusty, and scenario JSON.
   - **[person-3-dashboard-ui.md](person-3-dashboard-ui.md)** — Next.js 15 Old-West dashboard for policy authoring, approvals, audit, live activity, and evals.
   - **[person-4-adapters-openclaw-demo.md](person-4-adapters-openclaw-demo.md)** — adapter manifest, deterministic local adapters, OpenClaw bridge, and demo packaging.
4. Round-2 hackathon specs (active):
   - **[person-1-openclaw-bridge.md](person-1-openclaw-bridge.md)** — OpenClaw inbound translator, Kalshi-CLI capture, end-to-end smoke, prompt-injection scenario.

## Team

Four engineers, parallel work after the hour-0→2 contract freeze. Each spec is self-contained — the goal is zero improvisation.

## Product + demo

The product is now broader than the original hackathon framing:

1. Generate a starter policy from a user description of what the agent is for.
2. Edit and publish policy versions made of static rules plus a judge prompt.
3. Govern live tool calls through the gateway.
4. Replay historical audit rows against draft policies with eval runs.

The original three demo scenarios still remain the main smoke test and live-demo path:

1. **Good** — normal tool use is allowed.
2. **Injection** — a malicious or exfiltration-shaped action is denied.
3. **Approval** — a borderline action pauses for Sheriff review and then completes when approved.

Primary agent: OpenClaw (live). Fallback: Deputy Dusty CLI simulator.

## Next phase

After implementation, each person gets an `/orchestra` run file in [`../implementation/`](../implementation/) with intent-driven prompts for agent-assisted execution.
