"use client";

import { useMutation } from "@tanstack/react-query";
import { useShallow } from "zustand/shallow";
import { jailAgent, releaseAgent, revokeAgent } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { selectAgentsList, useAppStore } from "@/lib/store";
import type { AgentState, AgentStateDTO, Decision } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function DeputiesPage() {
  const agents = useAppStore(useShallow(selectAgentsList));
  return (
    <section>
      <PageHeader
        title="Deputies"
        subtitle={
          agents.length === 0
            ? "No agents on the roster"
            : `${agents.length} agent${agents.length === 1 ? "" : "s"} on the roster`
        }
      />

      {agents.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
          <p className="font-heading text-xl text-ink">No deputies reporting</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
            Agents appear here once they hit the gateway. Kick off a demo
            scenario to seed the roster.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => (
            <DeputyCard key={agent.agent_id} agent={agent} />
          ))}
        </div>
      )}
    </section>
  );
}

function DeputyCard({ agent }: { agent: AgentStateDTO }) {
  const jail = useMutation({ mutationFn: () => jailAgent(agent.agent_id) });
  const release = useMutation({ mutationFn: () => releaseAgent(agent.agent_id) });
  const revoke = useMutation({ mutationFn: () => revokeAgent(agent.agent_id) });

  const busy = jail.isPending || release.isPending || revoke.isPending;

  return (
    <div className="border border-brass/40 bg-parchment-deep/40 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <p className="font-heading text-lg text-ink">
            {agent.agent_label ?? agent.agent_id}
          </p>
          <p className="font-mono text-[10px] text-ink-soft">
            {agent.agent_id}
          </p>
        </div>
        <StateBadge state={agent.state} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 font-mono text-[11px]">
        <Stat label="Requests" value={agent.request_count} />
        <Stat label="Blocked" value={agent.blocked_count} accent="wanted" />
        <Stat
          label="Last decision"
          value={agent.last_decision ?? "—"}
          accent={
            agent.last_decision ? decisionAccent(agent.last_decision) : undefined
          }
        />
        <Stat
          label="Last seen"
          value={formatRelative(agent.last_seen_at)}
        />
      </div>

      {agent.active_policy_version_id && (
        <p className="mt-3 font-mono text-[10px] text-ink-soft">
          policy · <span className="text-ink">{agent.active_policy_version_id}</span>
        </p>
      )}

      <div className="mt-4 flex gap-2">
        <AgentBtn
          variant="neutral"
          disabled={busy || agent.state === "jailed"}
          onClick={() => jail.mutate()}
        >
          Jail
        </AgentBtn>
        <AgentBtn
          variant="neutral"
          disabled={busy || agent.state !== "jailed"}
          onClick={() => release.mutate()}
        >
          Release
        </AgentBtn>
        <AgentBtn
          variant="wanted"
          disabled={busy || agent.state === "revoked"}
          onClick={() => revoke.mutate()}
        >
          Revoke
        </AgentBtn>
      </div>
    </div>
  );
}

function StateBadge({ state }: { state: AgentState }) {
  const classes =
    state === "active"
      ? "border-brass-dark text-brass-dark"
      : state === "jailed"
        ? "border-approval-amber text-approval-amber"
        : state === "revoked"
          ? "border-wanted-red text-wanted-red"
          : "border-ink-soft text-ink-soft";
  return (
    <span
      className={cn(
        "border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        classes,
      )}
    >
      {state}
    </span>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: "wanted" | "amber" | "brass";
}) {
  const color =
    accent === "wanted"
      ? "text-wanted-red"
      : accent === "amber"
        ? "text-approval-amber"
        : accent === "brass"
          ? "text-brass-dark"
          : "text-ink";
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <div className={cn("mt-0.5 text-sm", color)}>{value}</div>
    </div>
  );
}

function AgentBtn({
  variant,
  ...rest
}: {
  variant: "neutral" | "wanted";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const base =
    "flex-1 border px-2 py-1.5 font-mono text-[10px] uppercase tracking-widest transition disabled:cursor-not-allowed disabled:opacity-40";
  const variantClass =
    variant === "wanted"
      ? "border-wanted-red text-wanted-red hover:bg-wanted-red/10"
      : "border-ink text-ink hover:bg-ink/5";
  return <button type="button" {...rest} className={cn(base, variantClass, rest.className)} />;
}

function decisionAccent(decision: Decision): "wanted" | "amber" | "brass" {
  return decision === "deny"
    ? "wanted"
    : decision === "approval_required"
      ? "amber"
      : "brass";
}

function formatRelative(iso: string | null): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diff = Date.now() - then;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}
