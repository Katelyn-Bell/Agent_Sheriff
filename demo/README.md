# AgentSheriff Demo

This directory packages the local AgentSheriff demo stack:

- backend gateway on `http://localhost:8000`
- frontend dashboard on `http://localhost:3000`
- optional OpenClaw container configured to call `POST /v1/tool-call`

## Run The Stack

```bash
demo/run-demo.sh
```

Run with OpenClaw included:

```bash
demo/run-demo.sh --with-openclaw
```

OpenClaw uses `demo/openclaw-config/tools.yaml` to normalize tool arguments and send all governed actions to the AgentSheriff gateway. The compose file uses the current OpenClaw GHCR image named in the OpenClaw Docker docs.

## Track A: Scenario Demo

This is the fast judge-facing path using the deterministic Deputy Dusty scenarios:

```bash
demo/smoke-test.sh
```

It runs:

1. `good` - creates a normal internal calendar event.
2. `injection` - attempts an exfiltration-shaped email and should be denied.
3. `approval` - sends a sensitive invoice attachment and should request approval.

The scenario fixtures live in `backend/src/agentsheriff/demo/scenarios`.

## Track B: Product Demo

This path shows the generalized product loop:

1. Open the dashboard at `http://localhost:3000`.
2. Generate a starter policy for the agent's job from the Town Laws flow.
3. Review and publish that policy.
4. Let OpenClaw call governed tools through `POST /v1/tool-call`.
5. Inspect the ledger and eval surfaces as decisions are recorded.

Example gateway call:

```bash
curl -sS http://localhost:8000/v1/tool-call \
  -H 'content-type: application/json' \
  -d '{
    "agent_id": "openclaw-demo",
    "agent_label": "OpenClaw Demo Agent",
    "tool": "files.read",
    "args": {"path": "readme.txt"},
    "context": {
      "task_id": "product-demo-files-read",
      "source_prompt": "Read the mock workspace readme.",
      "conversation_id": "product-demo"
    }
  }'
```

## Future Bridge Work

Transparent HTTP or proxy-style interception, inspired by CrabTrap, is a future integration path only. It is outside this MVP because it would require different infrastructure and security assumptions, including proxy routing, certificate handling, and stricter isolation boundaries.

The current MVP bridge is explicit tool-call governance through the Python gateway and deterministic local adapters.
