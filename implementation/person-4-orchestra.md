# Person 4 — Adapters, OpenClaw Integration, and Demo Packaging (Orchestra Run File)

**Owner:** Person 4
**Working directory:** `/Users/bernardorodrigues/Documents/Code/Agent_Sheriff`
**Branch:** `person-4/adapters-openclaw-demo`
**Spec:** [`../specs/person-4-adapters-openclaw-demo.md`](../specs/person-4-adapters-openclaw-demo.md)
**Shared context:** [`../specs/_shared-context.md`](../specs/_shared-context.md)
**Integration contract:** [`../specs/integration-and-handoffs.md`](../specs/integration-and-handoffs.md)

## How to use this file

Each Run should leave the rest of the team with a more complete executable edge: first the manifest and registry, then real adapters, then OpenClaw wiring, then demo packaging.

## Mission

Person 4 owns the executable surface:

- tool manifest
- adapter registry and local deterministic adapters
- OpenClaw bridge
- demo packaging for both scenario mode and general-purpose mode

---

## Run 1 — Tool manifest and registry

**Purpose.** Freeze the supported tool surface so the rest of the team can build against it.

### Agent 1A — Manifest and adapter registry

Implement:

- `backend/src/agentsheriff/adapters/manifest.py`
- `backend/src/agentsheriff/adapters/__init__.py`
- `backend/src/agentsheriff/adapters/_common.py`

Define the canonical catalog for at least:

- `gmail.*`
- `calendar.*`
- `files.*`
- `github.*`
- `browser.*`
- `shell.*`

Expose:

- `ALL_TOOLS`
- lookup helpers
- `DISPATCH`

Every adapter call must require `gateway_token`.

**Acceptance**

- backend can validate tool names from the manifest
- Person 2 can consume the manifest for starter policy generation

---

## Run 2 — Deterministic local adapters

**Purpose.** Replace stubs with stable local behavior that is safe for demos and testing.

### Agent 2A — Core adapters and seeding

Implement:

- `gmail.py`
- `calendar.py`
- `files.py`
- `_seed.py`

Support deterministic data, local mock filesystem use, and scenario compatibility.

**Acceptance**

- seeded local state is reproducible
- scenario-critical tools behave predictably

### Agent 2B — Remaining adapters and adapter tests

Implement:

- `github.py`
- `browser.py`
- `shell.py`
- `backend/tests/test_adapters.py`

Cover:

- token enforcement
- deterministic outputs
- path safety
- no uncontrolled side effects

**Acceptance**

- adapter tests pass
- all manifest-declared tools are reachable through `DISPATCH`

---

## Run 3 — OpenClaw bridge

**Purpose.** Point OpenClaw at the generalized tool-call gateway contract rather than the old scenario-only framing.

### Agent 3A — OpenClaw tools config and normalized gateway mapping

Implement:

- `demo/openclaw-config/tools.yaml`

Ensure every OpenClaw tool call maps cleanly to `POST /v1/tool-call` with stable:

- `agent_id`
- `agent_label`
- normalized args

Keep scenario prompts available for `good`, `injection`, and `approval`.

**Acceptance**

- OpenClaw can hit the generalized gateway contract
- scenario mode still works

---

## Run 4 — Demo packaging

**Purpose.** Make both the classic scenario demo and the broader product demo runnable by the team.

### Agent 4A — Compose, run scripts, and dual-track demo docs

Implement:

- `demo/docker-compose.yml`
- `demo/run-demo.sh`
- `demo/smoke-test.sh`
- `demo/README.md`

Document two flows:

1. **Scenario demo** using `good`, `injection`, and `approval`
2. **Product demo** showing starter policy generation, policy publish, governed OpenClaw calls, and audit/eval reflection

**Acceptance**

- compose brings up backend, frontend, and OpenClaw
- docs explain both tracks clearly

---

## Run 5 — Deferred bridge documentation

**Purpose.** Make the future boundary explicit so the team does not accidentally scope-creep into CrabTrap's proxy model during MVP.

### Agent 5A — Document future proxy-style bridge

Add a clear section in the demo or adapter docs describing a **future** bridge for transparent HTTP or proxy-style interception inspired by CrabTrap.

Document it only as:

- a future path
- outside MVP
- requiring different infrastructure and security assumptions

**Acceptance**

- no current file implies that HTTP MITM proxying already exists in the MVP

---

## Cross-team handoffs

- **To Person 1:** manifest, `DISPATCH`, stable adapter outputs
- **To Person 2:** manifest for policy generation, scenario compatibility
- **To Person 3:** human-readable tool metadata and result summaries

---

## Final acceptance

Person 4 is done when:

1. the tool surface is defined by a shared manifest
2. adapters are deterministic and safe
3. OpenClaw talks to the generalized gateway contract
4. the team can demo both scenario mode and general-purpose mode
5. future proxy-style interception is documented as later work, not implied MVP functionality
