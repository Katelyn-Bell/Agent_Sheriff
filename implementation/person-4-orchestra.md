# Person 4 — Adapters, OpenClaw & Demo (Orchestra Run File)

**Owner:** Person 4
**Working directory:** /Users/ianrowe/git/Agent_Sheriff
**Branch:** person-4/adapters-openclaw-demo
**Spec:** `specs/person-4-adapters-openclaw-demo.md`
**Shared context:** `specs/_shared-context.md`
**Reconciliation:** `specs/integration-and-handoffs.md`

## How to use this file
Each Run is a hard ordering boundary — finish all parallel agents in Run N (and pass its acceptance) before starting Run N+1. Within a Run, agents are designed on disjoint files so they can execute concurrently. Every prompt is self-contained: branch, files to touch, exact acceptance, and verification command. Cite the linked specs before improvising. The H-numbers (H0..H18) are hackathon hours — they bound elapsed wall time, not effort. Run 1 unblocks Person 1; Run 2 depends on Person 2's `scenarios/injection.json`; Run 3 depends on Person 1's `/health` route. Where a downstream contract is ambiguous, defer to `specs/integration-and-handoffs.md` rather than guessing.

## Assumptions
- Docker Desktop ≥ 4.27, `docker compose` v2.24+, `uv`, Python 3.11, Node 20.
- `GATEWAY_ADAPTER_SECRET` exported in local shell **and** present in `demo/.env` (gitignored).
- `AGENTSHERIFF_MOCK_FS` defaults differ: `./mock-fs` locally, `/app/mock-fs` inside Docker.
- No real credentials anywhere in the tree — only throwaway tokens / placeholders.
- Person 1's gateway is merged by Run 3; Person 2's `scenarios/injection.json` is merged by Run 2.

---

## Run 1 — Stub adapters + DISPATCH (H0→H2) — UNBLOCKS P1

**Purpose.** Person 1 can `from agentsheriff.adapters import DISPATCH` and call any tool without crashing. Establishes registry shape and gateway-token enforcement.
**Dependencies.** None.
**Parallel agents.** 1.

### Agent 1A — Stub all 6 adapters + DISPATCH + gitignore
**Prompt.** On branch `person-4/adapters-openclaw-demo`, create the adapter package skeleton at `backend/src/agentsheriff/adapters/` with files `_common.py`, `gmail.py`, `files.py`, `github.py`, `browser.py`, `shell.py`, `calendar.py`, and `__init__.py`. See `specs/person-4-adapters-openclaw-demo.md` §"Run 1" for the exact contract.

`_common.py` MUST expose: `MOCK_FS_ROOT` (read from env `AGENTSHERIFF_MOCK_FS`, default `./mock-fs`); `require_token(provided: str)` which uses `secrets.compare_digest` against env `GATEWAY_ADAPTER_SECRET` and raises `PermissionError` on mismatch — plain `==` is forbidden (timing attacks). At import time, if `GATEWAY_ADAPTER_SECRET` is unset, raise `RuntimeError("GATEWAY_ADAPTER_SECRET must be set")` so misconfigured deploys fail fast.

Each adapter module MUST export `SUPPORTED_TOOLS: list[str]` and `async def call(tool: str, args: dict, gateway_token: str) -> dict` returning `{"stub": True, "tool": tool, "args": args}` for now. Tool names follow `module.action` (e.g. `gmail.read_inbox`, `files.write`, `github.create_pr`, `browser.open_url`, `shell.run`, `calendar.create_event`). MUST INCLUDE `calendar` (`calendar.create_event`, `calendar.list_events`, `calendar.delete_event`) — Person 2's good-path scenario uses calendar in scene 1; omitting it breaks scene 1.

`__init__.py` builds `DISPATCH: dict[str, Callable]` as the union of every module's `SUPPORTED_TOOLS`, raising `ValueError` on duplicate keys. Also add a repo-root `.gitignore` covering `mock-fs/`, `demo/.env`, `**/sheriff.db`, `backend/data/`, `.next/`, `node_modules/`, `demo/run-*.log`, `demo/record-fallback.mp4`.

**Acceptance.** `python -c "from agentsheriff.adapters import DISPATCH; print(len(DISPATCH))"` prints ≥ 15. Unsetting `GATEWAY_ADAPTER_SECRET` then importing fails with the clear `RuntimeError`. **Verify.** `pytest -q backend/tests/test_imports.py` if present, otherwise the manual import check above.

---

## Run 2 — Real adapters + mock filesystem + seed + tests (H2→H8)

**Purpose.** Replace stubs with realistic fixture-backed implementations; seed reads `injection_payload` from Person 2's scenario file; pytest green.
**Dependencies.** Run 1 + `scenarios/injection.json` from Person 2.
**Parallel agents.** 2 (disjoint files).

### Agent 2A — gmail + files + calendar
**Prompt.** Implement `gmail.py`, `files.py`, `calendar.py` per `specs/person-4-adapters-openclaw-demo.md` §"Run 2". `gmail.read_inbox` returns 5 canned emails; one MUST embed `injection_payload` from `scenarios/injection.json` (lazy-read on first call with a `_DEFAULT_INJECTION` constant fallback so the module imports even if Person 2 hasn't merged yet). `gmail.send_email` writes RFC822 `.eml` to `MOCK_FS_ROOT/sent/`. `gmail.search` filters the canned inbox by query substring.

`files.read|write|list|delete` are sandboxed via a `safe_join(root, user_path)` helper rooted at `MOCK_FS_ROOT/home/user/`; any path that resolves outside the root MUST raise `PermissionError("path escape blocked")`. `calendar` is an in-memory dict (module-level) with `create_event`, `list_events`, `delete_event`.

Do NOT touch `github.py`, `browser.py`, `shell.py`, `_seed.py`, or `tests/` — Agent 2B owns those. **Acceptance.** Manual `python -c` exercising each adapter returns plausible data; injection payload visible in inbox row.

### Agent 2B — github + browser + shell + _seed.py + test_adapters.py
**Prompt.** Implement `github.py` with module-level `_REPO_STATE` dict and tools `list_prs`, `create_pr`, `push_branch` (record `force=True` flag in audit-friendly return), `comment`. `browser.open_url` loads fixture HTML from `MOCK_FS_ROOT/web/<host>/<path>.html`; seed `outlaw.html` with the same `injection_payload` source as gmail. `shell.run` MUST NEVER call `subprocess` — return a canned `{"stdout": ..., "exit_code": 0}` dict; this is enforced by test.

Create `backend/src/agentsheriff/adapters/_seed.py` runnable via `python -m agentsheriff.adapters._seed` — idempotent population of `mock-fs/` (home/user, sent/, web/, including `web/outlaw/injected-page.html`) reading `injection_payload` from `scenarios/injection.json`.

Create `backend/tests/test_adapters.py` with 8 tests: (1-6) token enforcement parametrized over the six adapter modules — wrong token raises, right token returns; (7) `files` path escape via `../../etc/passwd` raises `PermissionError`; (8) `shell.run` never invokes subprocess — use `unittest.mock.patch.object(subprocess, "run")` and assert `not_called`; plus DISPATCH covers all `SUPPORTED_TOOLS`, github force-push flag recorded, gmail injection marker present.

**Acceptance.** `pytest -q backend/tests/test_adapters.py` exits 0; `python -m agentsheriff.adapters._seed` run twice yields identical `mock-fs/` tree.

---

## Run 3 — Docker Compose + Dockerfiles + run-demo/smoke-test (H8→H12)

**Purpose.** `docker compose up --build` brings backend + frontend healthy in < 60s. Narrow bind mounts only. Browser-facing URLs use the host, not the Docker network.
**Dependencies.** Run 2 + Person 1's `/health` endpoint.
**Parallel agents.** 1.

### Agent 3A — Dockerfiles, compose, env.example, scripts
**Prompt.** Per `specs/person-4-adapters-openclaw-demo.md` §"Run 3":

`backend/Dockerfile` on `python:3.11-slim` with `uv` installed; copy `pyproject.toml`+`uv.lock` first, run `uv sync --frozen --no-dev`, then copy source — keeps the dep layer cached. `CMD ["uvicorn", "agentsheriff.app:app", "--host", "0.0.0.0", "--port", "8000"]`.

`frontend/Dockerfile` multi-stage `node:20-alpine` (`deps` → `builder` → `runner`); declare `ARG NEXT_PUBLIC_API_BASE` and `ARG NEXT_PUBLIC_WS_URL` in the `builder` stage so they're baked into the static bundle.

`demo/docker-compose.yml`:
- `backend`: build from `../backend`, env `GATEWAY_ADAPTER_SECRET` and `ANTHROPIC_API_KEY` from `.env`, healthcheck `curl -f http://localhost:8000/health`, ports `8000:8000`. Volumes are NARROW: `./mock-fs:/app/mock-fs` and `./data:/app/data`. **No named volume over `/app`** — that foot-gun shadows the source baked into the image.
- `frontend`: build args `NEXT_PUBLIC_API_BASE=http://localhost:8000` and `NEXT_PUBLIC_WS_URL=ws://localhost:8000/v1/stream` — **HOST URLs**, because the browser runs on the host, not inside the Docker network. `depends_on: backend: { condition: service_healthy }`, ports `3000:3000`.
- Bridge network `sheriff-net`.

`demo/.env.example` with 7 required vars: `GATEWAY_ADAPTER_SECRET`, `ANTHROPIC_API_KEY`, `AGENTSHERIFF_MOCK_FS=/app/mock-fs`, `OPENCLAW_LLM_API_KEY`, `OPENCLAW_LLM_MODEL=claude-sonnet-4-6`, `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_WS_URL`.

`demo/run-demo.sh`: `docker compose up --build -d`, poll `/health` until 200, run `_seed`, print "READY". Does NOT start Dusty — that's Person 0's split.
`demo/smoke-test.sh`: runs `dusty --all`; refuses (exit 2) if `openclaw` container is running, to keep eval clean.

**Acceptance.** Clean checkout, `.env` filled with 2 real secrets, `cd demo && ./run-demo.sh` healthy in < 60s; `curl localhost:8000/health` 200; `curl localhost:3000` 200.

---

## Run 4 — OpenClaw bring-up + tools.yaml (H12→H16)

**Purpose.** OpenClaw proxies every tool to `http://backend:8000/v1/tool-call`. Three scripted prompts produce the expected sheriff decisions.
**Dependencies.** Run 3.
**Parallel agents.** 1.

### Agent 4A — OpenClaw service + tools.yaml + scene prompts + H14 freeze gate
**Prompt.** Per `specs/person-4-adapters-openclaw-demo.md` §"Run 4":

Pin the OpenClaw image: first try `ghcr.io/openclaw/openclaw:0.4` and capture the digest in `demo/docker-compose.yml` (`image: ghcr.io/openclaw/openclaw@sha256:...`). If that tag doesn't exist, build locally as `agentsheriff/openclaw:local` from the upstream source and reference that.

Add an `openclaw` service to `demo/docker-compose.yml`:
- env: `OPENCLAW_TOOLS_PATH=/config/tools.yaml`, `OPENCLAW_LLM_API_KEY=${ANTHROPIC_API_KEY}`, `OPENCLAW_LLM_MODEL=claude-sonnet-4-6`, plus empty throwaway tokens for every external integration OpenClaw probes at boot (`OPENCLAW_GMAIL_TOKEN=""`, `OPENCLAW_GITHUB_TOKEN=""`, etc.) so it doesn't refuse to start.
- volume `./openclaw-config:/config:ro`.
- `depends_on: backend: { condition: service_healthy }`.
- `command: ["sleep", "infinity"]` — we run agents via `docker compose exec` per scene, not as a long-lived service.

Create `demo/openclaw-config/tools.yaml` mapping every tool (`gmail.*`, `files.*`, `github.*`, `browser.*`, `shell.run`, `calendar.*`) to `POST http://backend:8000/v1/tool-call` — note **container network** name `backend`, NOT `localhost`. Pass `gateway_token: ${GATEWAY_ADAPTER_SECRET}` in the tool call body.

Create `demo/scene1.txt`, `demo/scene2.txt`, `demo/scene3.txt` with the exact verbatim user prompts from `specs/_shared-context.md` scene definitions.

Smoke test: `docker compose exec openclaw openclaw agent run --prompt "$(cat demo/scene1.txt)"` should result in at least one `POST /v1/tool-call` arriving at backend (verify via backend audit log row count delta).

**H14 FREEZE GATE.** If scenes 2 or 3 fail end-to-end via OpenClaw on two consecutive attempts, freeze on Dusty for the live demo, document the demotion in `demo/README.md`, and reference it only at slide level.

**Acceptance.** All 3 scenes produce expected audit rows via OpenClaw, OR the team explicitly agrees to freeze on Dusty.

---

## Run 5 — Demo packaging (H16→H18)

**Purpose.** Runbook, deck, 90-second pitch script, fallback recording, two rehearsals.
**Dependencies.** Run 4.
**Parallel agents.** 1.

### Agent 5A — Runbook + deck + pitch script + fallback recording + rehearsals
**Prompt.** Per `specs/person-4-adapters-openclaw-demo.md` §"Run 5":

Write `demo/README.md` as the runbook with a strict timeline: T-60 venue setup (terminal layout: window 1 = backend logs, window 2 = sheriff UI, window 3 = OpenClaw exec, window 4 = audit query), T-15 bring-up via `./run-demo.sh`, T-5 smoke via `./smoke-test.sh` (with `openclaw` stopped — required), showtime sequence with per-scene timing cues, an "if-fails" playbook (network down, OpenClaw refuses, Anthropic 429), and a 12-item pre-demo checklist (`.env` filled, mock-fs seeded, video on USB stick, etc.).

Write `demo/pitch/deck-outline.md` — 5 slides: (1) title, (2) problem, (3) product with a one-paragraph architecture diagram description, (4) live-demo lockup (says "switch to terminal"), (5) what's next.

Write `demo/pitch/script-90s.md` — word-for-word 90s narration, with timing cues `[00:00-00:08]`, `[00:08-00:20]`, etc., and "sacrificial phrases" marked `(*cut if running long*)` so we can hit 90s ± 5s under stress.

Record `demo/record-fallback.mp4` via OBS at 1080p60, H.264 CRF 22, AAC 192 kbps, ≤ 2:00. Read the script aloud while triggering scenes 1-3 live. The MP4 is gitignored (already added in Run 1) — store on the team drive and link from `demo/README.md`.

Run 2 rehearsals; aim for 90s ± 5s. Log timings + flubs to `demo/pitch/rehearsal-notes.md`.

**Acceptance.** All files exist; `demo/record-fallback.mp4` plays and is ≤ 2:00 at ≥ 1080p; the 12-item checklist has ≥ 12 unchecked boxes pre-demo; `grep -RIn -E '(sk-ant-|ghp_|AKIA[0-9A-Z]{16})' demo/ backend/ frontend/` returns empty.

---

## Integration checkpoint (gate for squash-merge to main)

Reviewer verifies on a clean checkout of `person-4/adapters-openclaw-demo`:

1. `cp demo/.env.example demo/.env`, fill the 2 real secrets (`ANTHROPIC_API_KEY`, `GATEWAY_ADAPTER_SECRET`); `docker compose -f demo/docker-compose.yml up --build` healthy in < 60s.
2. All 3 scenes pass via OpenClaw, OR Dusty fallback (Dusty is the floor — never below).
3. `demo/record-fallback.mp4` exists, plays, ≤ 2:00, ≥ 1080p.
4. `grep -RIn -E '(sk-ant-|ghp_|AKIA[0-9A-Z]{16})' demo/ backend/ frontend/` returns empty.
5. `pytest backend/tests/test_adapters.py -q` exits 0.
6. `demo/.env` is gitignored and NOT committed (`git ls-files demo/.env` empty).
