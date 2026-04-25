# Person 4 — Adapters, OpenClaw Integration, and Demo Packaging

> Owner: Person 4
> Primary directories: `backend/src/agentsheriff/adapters/` and `demo/`
> Read [`specs/_shared-context.md`](./_shared-context.md) and [`specs/integration-and-handoffs.md`](./integration-and-handoffs.md) first.

## Mission

Own the executable edge of AgentSheriff:

- the adapter layer that actually performs mock tool actions
- the reusable tool manifest that describes those actions
- OpenClaw integration against the generalized gateway contract
- demo packaging for both scenario mode and general-purpose mode

Your scope is no longer just "mock tools for three scenes". It is the reusable tool surface that lets the policy gateway govern real agent workflows in a controlled local environment.

## Core responsibilities

### 1. Adapter manifest

Create and own a canonical tool manifest that describes the supported tool-call surface.

At minimum, it should cover:

- tool id
- namespace
- human label
- risk hints
- argument schema summary
- whether results are replay-safe

This manifest should be consumable by:

- Person 1 for validation and gateway behavior
- Person 2 for starter policy generation
- Person 3 for descriptive UI labels
- OpenClaw tool wiring

### 2. Adapters

Own deterministic local adapters for the MVP tool surface.

Suggested namespaces:

- `gmail.*`
- `calendar.*`
- `files.*`
- `github.*`
- `browser.*`
- `shell.*`

These remain mock or local-only for MVP. No uncontrolled real side effects.

### 3. OpenClaw bridge

Point OpenClaw at the generalized `POST /v1/tool-call` contract.

The OpenClaw integration should work for:

- scenario mode
- ad hoc tool use against the local adapter surface

### 4. Demo packaging

Package the stack so both modes are demoable:

- scenario-driven demo
- general gateway workflow demo

## Deliverables

```text
backend/src/agentsheriff/adapters/
├── __init__.py
├── manifest.py
├── _common.py
├── gmail.py
├── calendar.py
├── files.py
├── github.py
├── browser.py
├── shell.py
└── _seed.py

backend/tests/
└── test_adapters.py

demo/
├── docker-compose.yml
├── openclaw-config/
│   └── tools.yaml
├── README.md
├── run-demo.sh
└── smoke-test.sh
```

## 1. Adapter design rules

- no real third-party side effects in MVP
- deterministic outputs
- explicit `gateway_token` enforcement
- stable tool ids
- all adapter outputs should be easy to summarize in the ledger

### Security seam

`GATEWAY_ADAPTER_SECRET` remains the only gateway-to-adapter auth primitive for MVP.

Every public adapter call must require and validate `gateway_token`.

## 2. Tool manifest

Implement `manifest.py` as the single catalog of supported tool names.

Suggested shape:

```python
ToolDefinition(
    id="gmail.send_email",
    namespace="gmail",
    label="Send email",
    risk_hints=["external_recipient", "sensitive_attachment"],
    args_schema_summary={...},
)
```

Expose:

- `ALL_TOOLS`
- lookup by tool id
- namespace grouping helpers

Do not let the backend and OpenClaw each invent their own tool lists.

## 3. Adapter registry

`adapters/__init__.py` should export:

- `DISPATCH`
- manifest helpers where useful

Person 1 expects to call `DISPATCH[tool](tool, args, gateway_token=...)`.

## 4. OpenClaw integration

OpenClaw should talk to the generalized gateway contract, not a scenario-only shape.

### Required properties

- every OpenClaw tool call maps cleanly to `ToolCallRequest`
- `agent_id` and `agent_label` remain stable
- tool arguments are normalized before hitting the gateway
- prompt-only scenario wrappers remain available for demos

### Scenario mode

Keep prompts or scripts for:

- `good`
- `injection`
- `approval`

### General-purpose mode

Add a documented flow where a user can:

1. generate a starter policy
2. publish it
3. let OpenClaw operate against the governed local tool set

## 5. Demo packaging expectations

`demo/docker-compose.yml` should support:

- backend
- frontend
- OpenClaw

`demo/README.md` should explain two demo tracks:

### Track A: Scenario demo

Fast, dramatic, reliable. Uses `good`, `injection`, and `approval`.

### Track B: Product demo

Shows the generalized workflow:

1. user describes what the agent is for
2. starter policy is generated
3. user edits or publishes it
4. OpenClaw performs governed tool calls
5. audit and eval surfaces reflect the behavior

## 6. Future bridge work, explicitly deferred

You should mention, but **not implement for MVP**, a later bridge layer for transparent HTTP or proxy-style interception inspired by CrabTrap.

Document it as:

- a future integration path
- outside current implementation scope
- likely requiring different infrastructure and security assumptions

Do not imply it is already part of the Python gateway MVP.

## 7. Integration contracts

### With Person 1

Provide:

- stable `DISPATCH`
- stable tool manifest
- deterministic adapter outputs

### With Person 2

Provide:

- manifest input for starter policy generation
- scenario compatibility with risk heuristics

### With Person 3

Provide:

- human-readable tool metadata for UI
- execution result shapes that can be summarized cleanly

## 8. Tests

Write adapter tests for:

- registry completeness
- token enforcement
- deterministic output
- path safety for file operations
- scenario-critical tools like `gmail.send_email`, `files.read`, `calendar.create_event`

## 9. Acceptance criteria

You are done when:

- the adapter surface is described by a shared manifest
- OpenClaw can hit the generalized gateway contract
- scenario mode still works
- the demo stack can show both scenario and general-purpose product flows
- transparent HTTP proxying is clearly documented as later work, not silently mixed into MVP

## 10. Explicit non-goals

Do not take ownership of:

- gateway decision logic
- policy generation logic quality
- dashboard implementation
- a true HTTP/HTTPS MITM proxy in this phase
