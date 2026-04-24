# AgentSheriff — Specs

Hackathon spec set for **AgentSheriff**: an identity, permission, and safety firewall for AI agents. Sits between agents (OpenClaw, etc.) and the tools they call (email, files, shell, GitHub, browser) and decides **allow / deny / require human approval** based on YAML policies + threat detection.

## Read order

1. **[_shared-context.md](_shared-context.md)** — product, demo, tech stack, locked repo layout, API contracts. Ground truth for everything else.
2. **[integration-and-handoffs.md](integration-and-handoffs.md)** — cross-team contract audit, data-flow diagrams for the 3 demo scenarios, env var catalog, hour-by-hour milestones, dependency blockers, acceptance matrix, gap log.
3. Per-person specs (pick your own):
   - **[person-1-backend-core.md](person-1-backend-core.md)** — FastAPI gateway, policy engine, audit store, approvals queue, WebSocket streams.
   - **[person-2-threats-simulator.md](person-2-threats-simulator.md)** — threat detector, Claude Haiku/Sonnet classifier, Deputy Dusty demo simulator, scenario JSON.
   - **[person-3-dashboard-ui.md](person-3-dashboard-ui.md)** — Next.js 15 Old-West-themed dashboard (6 pages + components).
   - **[person-4-adapters-openclaw-demo.md](person-4-adapters-openclaw-demo.md)** — mock tool adapters, OpenClaw Docker Compose bring-up, demo runbook, pitch deck.

## Team

Four engineers, parallel work after the hour-0→2 contract freeze. Each spec is self-contained — the goal is zero improvisation.

## Demo (north star)

Three scenes, back-to-back in under 60 seconds:
1. **Good** — agent reads email, creates calendar event → allowed.
2. **Injection** — agent tries to exfiltrate contacts to an outlaw address → denied, Wanted Poster slams in, deputy jailed.
3. **Approval** — agent tries to email an invoice to the accountant → requires Sheriff approval; Sheriff clicks Approve; action completes.

Primary agent: OpenClaw (live). Fallback: Deputy Dusty CLI simulator.

## Next phase

After implementation, each person gets an `/orchestra` run file in [`../implementation/`](../implementation/) with intent-driven prompts for agent-assisted execution.
