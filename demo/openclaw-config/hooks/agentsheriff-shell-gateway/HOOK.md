---
name: agentsheriff-shell-gateway
description: "Route OpenClaw exec/bash tool calls through AgentSheriff before execution"
metadata:
  openclaw:
    emoji: "🛡️"
    events: ["before_tool_call"]
---

# AgentSheriff Shell Gateway Hook

Rewrites OpenClaw `exec` and `bash` tool calls so the command runs through
`demo/openclaw-config/bin/agentsheriff-shell`. The wrapper posts the original
command to AgentSheriff's `/v1/openclaw/tool-call` endpoint, prints the approved
command output back to OpenClaw, and exits non-zero when AgentSheriff denies it.
