# Person 1 — OpenClaw Bridge Spec (Hackathon Round 2)

> Owner: Person 1
> Primary directories: `backend/src/agentsheriff/openclaw/` (new), `demo/openclaw-config/`, `demo/openclaw-config/fixtures/` (new)
> Read [`specs/_shared-context.md`](./_shared-context.md), [`specs/integration-and-handoffs.md`](./integration-and-handoffs.md), and [`specs/person-1-backend-core.md`](./person-1-backend-core.md) (already shipped) first.
>
> This spec **supersedes** the original `person-1-backend-core.md` for the round-2 hackathon push. The backend core work is done (gateway, policy engine, audit, approvals, streams). Person 3 also shipped the `skill_id` plumbing (PR #22) — your translator will populate that field.

## Mission

Make a real OpenClaw agent fire a real Kalshi tool call, get governed by AgentSheriff, and show up live on the dashboard. End-to-end, with no mocked layers between OpenClaw and the gateway.

You own:

- the inbound translator that catches OpenClaw's outbound tool calls and reshapes them into our `POST /v1/tool-call` envelope
- a stub OpenClaw skill fixture that unblocks Persons 2 and 4 in the first 60 minutes
- the local OpenClaw + Kalshi-CLI install + auth flow
- the captured tool-call fixtures used as test data and fallback for the demo
- the Day-2 prompt-injection scenario

You do **not** own:

- `GET /v1/skills` endpoint or SKILL.md parsing (Person 2)
- LLM-generated user preferences flow (Person 2)
- new-policy wizard / skill picker UI (Person 4)
- backend gateway, policy engine, or `skill_id` field plumbing (already shipped)

## Architecture you are implementing

```
[user prompt]
     │
     ▼
[OpenClaw runtime] ── runs Kalshi skill from SKILL.md
     │
     │  outbound tool call (OpenClaw native shape)
     ▼
[INBOUND TRANSLATOR] ── you build this
     │
     │  POST /v1/tool-call with:
     │   - tool: "shell.run"
     │   - args: { command: "kalshi-cli ..." }
     │   - context.skill_id: "kalshi-trading"
     │   - context.task_id, source_prompt, source_content
     ▼
[gateway.handle_tool_call] ── already shipped
     │
     ├──▶ threats / policy / approval / audit
     ├──▶ hub.broadcast_nowait(...) → dashboard updates live
     └──▶ ToolCallResponse {decision, reason, audit_id, approval_id, result}
     │
     ▼
[INBOUND TRANSLATOR] ── reshape response into OpenClaw's expected shape
     │
     ▼
[OpenClaw runtime] ── proceeds or aborts based on decision
```

The Kalshi skill is a thin wrapper around the `kalshi-cli` shell command (see [`SKILL.md`](https://github.com/lacymorrow/openclaw-kalshi-trading-skill/blob/main/SKILL.md)). Every OpenClaw tool call from this skill ultimately becomes a `kalshi-cli ...` invocation. The simplest interception strategy: **all Kalshi traffic surfaces as our existing `shell.run` tool**, with `context.skill_id="kalshi-trading"` so policies can scope to it.

## Hard contracts you must honor

These are frozen — Person 3 already shipped the receiving end.

- **Endpoint**: `POST /v1/tool-call` (FastAPI, no auth wall yet)
- **Request DTO** (`backend/src/agentsheriff/models/dto.py:ToolCallRequest`):
  ```json
  {
    "agent_id": "openclaw_kalshi",
    "agent_label": "Kalshi Trader",
    "tool": "shell.run",
    "args": { "command": "kalshi-cli orders create --market ... --side yes --qty 10 --price 50" },
    "context": {
      "task_id": "<openclaw-task-id>",
      "source_prompt": "<user's original prompt>",
      "source_content": "<any external content the agent ingested>",
      "conversation_id": "<openclaw conversation id>",
      "skill_id": "kalshi-trading"
    }
  }
  ```
- **Response DTO** (`ToolCallResponse`): `{decision, reason, risk_score, audit_id, approval_id, result, ...}`. `decision` is one of `"allow" | "deny" | "approval_required"`. On approval the gateway blocks until human resolution (default 60s timeout).
- **`skill_id` value**: must be exactly `"kalshi-trading"` (matches the SKILL.md `name` frontmatter). Person 2's policies bind to this string.
- **`agent_id` value**: stable per OpenClaw conversation, e.g. `"openclaw_kalshi"`. Person 3's first-touch emit means the deputy will appear on the Wanted page on the FIRST call — don't change `agent_id` between calls within the same demo.

## Deliverables

### Hour 0 (60-minute deliverable — UNBLOCKS THE TEAM)

`demo/openclaw-config/fixtures/kalshi-skill-stub.json` — a guessed-but-plausible OpenClaw skill descriptor matching the SKILL.md frontmatter. Persons 2 and 4 build against this until you replace it with a real captured fixture. Minimal shape:

```json
{
  "id": "kalshi-trading",
  "name": "Kalshi Trading",
  "description": "...",
  "metadata": { "openclaw": { "requires": { "bins": ["kalshi-cli"] } } },
  "commands": [
    "kalshi-cli markets list",
    "kalshi-cli markets get",
    "kalshi-cli markets orderbook",
    "kalshi-cli orders create",
    "kalshi-cli orders cancel",
    "kalshi-cli orders cancel-all",
    "kalshi-cli portfolio balance",
    "kalshi-cli portfolio positions",
    "kalshi-cli portfolio subaccounts transfer"
  ],
  "risky_flags": ["--prod", "cancel-all"]
}
```

Push to `main` directly so Person 2's `/v1/skills` work and Person 4's wizard mock can start immediately.

### Hours 1–4 — OpenClaw recon

1. `brew install 6missedcalls/tap/kalshi-cli` and `kalshi-cli auth login` with the team's existing API key. Verify `kalshi-cli markets list` returns demo-mode data.
2. Install OpenClaw locally per its docs. Install the Kalshi skill (`openclaw-kalshi-trading-skill`).
3. Run a low-stakes prompt: *"What Kalshi markets are open in the Crypto category?"*
4. Capture the OpenClaw outbound HTTP request (or stdio call) using mitmproxy / `tcpdump` / OpenClaw's own debug logs. Save the raw payload to `demo/openclaw-config/fixtures/openclaw-call-1.json`.
5. Repeat for: a `kalshi-cli orders create` flow and a `kalshi-cli portfolio balance` flow. Three real fixtures.

### Hours 4–10 — Inbound translator

Create `backend/src/agentsheriff/openclaw/translator.py` (and matching tests):

- Accepts an OpenClaw outbound payload (Pydantic model — define `OpenClawCallEnvelope` based on the captured fixtures)
- Returns a valid `ToolCallRequest` with the contract above
- Always sets `context.skill_id = "kalshi-trading"` for now (hardcoded; later sourced from OpenClaw's skill registry)
- Maps OpenClaw's tool/argument shape to `tool="shell.run"` + `args={"command": "<rebuilt kalshi-cli string>"}`

Create `backend/src/agentsheriff/api/openclaw.py` — a `POST /v1/openclaw/tool-call` endpoint that:
1. Receives the OpenClaw native envelope
2. Calls the translator
3. Forwards to `gateway.handle_tool_call(...)` (the existing function — do NOT reimplement)
4. Reshapes the `ToolCallResponse` back into OpenClaw's expected shape

Wire OpenClaw to point at this endpoint.

### Hours 10–12 — End-to-end smoke

- Boot backend + frontend.
- From OpenClaw, run the prompt: *"Show me the order book for KXBTC-26FEB12-B97000"*
- Confirm:
  - Dashboard `/wanted` shows "Kalshi Trader" deputy on first call (Person 3's first-touch emit)
  - Dashboard `/ledger` shows the audit row in real-time (Person 3's WS broadcast)
  - The OpenClaw response contains the actual Kalshi order book data
- Record a screen capture as the demo backup.

### Day 2 — Prompt-injection scenario (if time)

Build `demo/openclaw-config/fixtures/research-note-injection.md` — a fake research feed containing hidden instructions that try to force `kalshi-cli --prod orders create --qty 10000`. Wire it into one of the demo scripts under `demo/run-demo.sh` so the demo can play the injection live.

## Bailout plan (decide by hour 6)

If OpenClaw isn't configurable to redirect HTTP traffic, OR if the Kalshi skill turns out to be opaque:

1. **Plan B**: monkey-patch OpenClaw's HTTP client at startup to intercept the outbound call. ~3 hours.
2. **Plan C**: write a wrapper script `demo/openclaw-runner.py` that takes the user prompt, runs `kalshi-cli` directly with the same arguments OpenClaw would, and POSTs to `/v1/openclaw/tool-call` first. The demo story is identical — judges won't know. ~2 hours.

Pre-decide the bailout in writing before hour 6. Don't improvise on stage.

## Tests

Add `backend/tests/test_openclaw_translator.py`:

- `test_translator_emits_skill_id_in_context` — input a captured OpenClaw fixture; assert `output.context.skill_id == "kalshi-trading"`
- `test_translator_maps_kalshi_orders_create_to_shell_run` — assert `tool == "shell.run"` and `args["command"]` starts with `kalshi-cli orders create`
- `test_translator_preserves_agent_id_across_calls` — same OpenClaw conversation_id → same `agent_id` (so first-touch emit fires once, then deputy is reused)
- `test_openclaw_endpoint_forwards_to_gateway_and_returns_decision` — integration test that POSTs to `/v1/openclaw/tool-call` and asserts a real `ToolCallResponse` shape comes back

## Files you'll create or touch

```text
backend/src/agentsheriff/
├── openclaw/                     ← NEW (your module)
│   ├── __init__.py
│   ├── translator.py
│   └── envelope.py               ← Pydantic model for OpenClaw native shape
├── api/
│   └── openclaw.py               ← NEW (POST /v1/openclaw/tool-call)
└── main.py                       ← register the new router

backend/tests/
└── test_openclaw_translator.py   ← NEW

demo/openclaw-config/
├── fixtures/                     ← NEW
│   ├── kalshi-skill-stub.json    ← HOUR-0 deliverable
│   ├── openclaw-call-1.json
│   ├── openclaw-call-2.json
│   ├── openclaw-call-3.json
│   └── research-note-injection.md
└── tools.yaml                    ← update if OpenClaw config needs a custom endpoint URL

demo/
├── openclaw-runner.py            ← NEW (only if Plan C bailout)
└── run-demo.sh                   ← update to call OpenClaw flow
```

## Definition of done

1. ✅ Stub fixture pushed to `main` within 60 minutes of starting (Persons 2 + 4 unblocked).
2. ✅ At least one captured OpenClaw payload exists in `demo/openclaw-config/fixtures/`.
3. ✅ `backend/tests/test_openclaw_translator.py` passes via `uv run pytest`.
4. ✅ A real OpenClaw tool call (or Plan C wrapper) lands an audit row in the AgentSheriff ledger live.
5. ✅ Kalshi Trader deputy appears on the Wanted page on first call (no manual seeding needed).
6. ✅ A skill-bound policy authored by Person 2 (e.g. "deny `--prod` flag") actually denies the OpenClaw call when triggered.
7. ✅ Demo recording exists as a backup before final rehearsal.

## Hand-offs

- **Person 2 (skill reader)**: your `/v1/skills` endpoint should return at least one entry with `id="kalshi-trading"` matching what my translator injects. Use the hour-0 stub fixture as your source of truth until I capture real OpenClaw output.
- **Person 4 (wizard)**: the skill picker on the new-policy page should display "Kalshi Trading" with `id="kalshi-trading"` as a selectable option. Generated rules will carry `skill_match: {kind: "exact", value: "kalshi-trading"}` (Person 3's contract).
- **Whole team**: at hour 4, I'll either confirm the real OpenClaw path works or declare the bailout — sync briefly so Person 2 and 4 don't waste time on doomed integration paths.

## Risk register

| Risk | Mitigation |
|------|-----------|
| OpenClaw's outbound HTTP client isn't configurable | Plan B (monkey-patch) at hour 6 |
| OpenClaw install requires GPU / OS we don't have | Plan C wrapper — works without OpenClaw at all |
| Kalshi `--prod` API rate-limits the demo | Stay in demo mode (default), use mock balance for stage |
| OpenClaw payload differs wildly from guess | Stub fixture marked as guessed; rebase Persons 2/4 once real fixture lands |
| First-touch emit doesn't fire (Person 3's code) | Already verified by `test_gateway_first_touch_emits_agent_state_frame` — green |
