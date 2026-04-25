import path from "node:path";
import { fileURLToPath } from "node:url";

const WRAPPER_PATH = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../bin/agentsheriff-shell",
);

const SHELL_TOOL_NAMES = new Set([
  "exec",
  "bash",
  "sh",
  "shell",
  "run",
  "terminal",
  "shell.run",
  "shell.exec",
  "run_command",
  "run_shell_command",
  "run_in_terminal",
]);

const SHELL_TOOL_SUFFIX_RE = /(?:^|\.)(?:exec|bash|sh|shell|run|terminal)$/;

function isShellToolName(toolName) {
  if (!toolName) return false;
  if (SHELL_TOOL_NAMES.has(toolName)) return true;
  return SHELL_TOOL_SUFFIX_RE.test(toolName);
}

function quote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function b64(value) {
  return Buffer.from(String(value), "utf8").toString("base64url");
}

async function beforeToolCall(event, ctx) {
  const toolName = String(event?.toolName ?? "").toLowerCase();
  if (!isShellToolName(toolName)) return;
  if (process.env.AGENTSHERIFF_OPENCLAW_SHELL_HOOK_DISABLE === "1") return;

  const params = event?.params && typeof event.params === "object" ? event.params : {};
  const hasCommand = typeof params.command === "string";
  const hasCmd = typeof params.cmd === "string";
  const command = hasCommand ? params.command : hasCmd ? params.cmd : "";
  if (!command.trim()) return;
  if (command.includes("agentsheriff-shell")) return;

  const wrapped = [
    quote(WRAPPER_PATH),
    "--command-b64",
    quote(b64(command)),
    "--tool",
    quote(toolName),
    "--session",
    quote(String(ctx?.sessionKey ?? ctx?.sessionId ?? "")),
    "--run-id",
    quote(String(ctx?.runId ?? event?.runId ?? "")),
    "--tool-call-id",
    quote(String(ctx?.toolCallId ?? event?.toolCallId ?? "")),
  ];

  if (typeof params.workdir === "string" && params.workdir.trim()) {
    wrapped.push("--cwd-b64", quote(b64(params.workdir)));
  }

  const wrappedCommand = wrapped.join(" ");

  return {
    params: {
      ...params,
      ...(hasCommand || !hasCmd ? { command: wrappedCommand } : {}),
      ...(hasCmd ? { cmd: wrappedCommand } : {}),
      env: {
        ...(params.env && typeof params.env === "object" ? params.env : {}),
        AGENTSHERIFF_GATEWAY_URL:
          process.env.AGENTSHERIFF_GATEWAY_URL ?? "http://127.0.0.1:8000",
      },
    },
  };
}

const plugin = {
  id: "agentsheriff-shell-gateway",
  name: "AgentSheriff Shell Gateway",
  description: "Route OpenClaw exec/bash tool calls through AgentSheriff before execution",
  register(api) {
    api.on("before_tool_call", beforeToolCall);
  },
};

export default plugin;
