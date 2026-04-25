"use client";

import { useMutation } from "@tanstack/react-query";
import { useShallow } from "zustand/shallow";
import { Lock, Unlock, Ban, ShieldCheck } from "lucide-react";
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
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
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
  const label = agent.agent_label ?? agent.agent_id;
  const isFresh = agent.request_count === 0 && !agent.last_seen_at;

  return (
    <article
      className={cn(
        "flex flex-col overflow-hidden border-2 bg-parchment-deep/40 transition hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(43,24,16,0.15)]",
        agent.state === "revoked"
          ? "border-wanted-red/50"
          : agent.state === "jailed"
            ? "border-approval-amber/60"
            : "border-brass/50",
      )}
    >
      <header className="flex items-start gap-3 border-b border-brass/30 bg-parchment px-4 py-3">
        <DeputyBadge label={label} state={agent.state} />
        <div className="min-w-0 flex-1">
          <p className="truncate font-heading text-lg leading-tight text-ink">
            {label}
          </p>
          <p className="truncate font-mono text-[10px] text-ink-soft">
            {agent.agent_id}
          </p>
        </div>
        <StateBadge state={agent.state} />
      </header>

      {isFresh ? (
        <div className="flex flex-1 flex-col items-center justify-center px-4 py-8 text-center">
          <ShieldCheck className="h-7 w-7 text-brass-dark/60" />
          <p className="mt-2 font-heading text-sm text-ink">Sworn in, not on duty</p>
          <p className="mt-1 max-w-[28ch] text-xs text-ink-soft">
            Awaiting first request. Stats appear once this deputy starts
            calling tools.
          </p>
        </div>
      ) : (
        <div className="flex-1 px-4 py-3">
          <div className="grid grid-cols-2 gap-x-3 gap-y-3 font-mono text-[11px]">
            <Stat label="Requests" value={agent.request_count} />
            <Stat
              label="Blocked"
              value={agent.blocked_count}
              accent={agent.blocked_count > 0 ? "wanted" : undefined}
            />
            <Stat
              label="Last decision"
              value={agent.last_decision ?? "—"}
              accent={
                agent.last_decision ? decisionAccent(agent.last_decision) : undefined
              }
            />
            <Stat label="Last seen" value={formatRelative(agent.last_seen_at)} />
          </div>

          {agent.active_policy_version_id && (
            <p className="mt-3 truncate font-mono text-[10px] text-ink-soft">
              policy ·{" "}
              <span className="text-ink">{agent.active_policy_version_id}</span>
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-3 gap-px border-t border-brass/30 bg-brass/30">
        <AgentBtn
          variant="neutral"
          icon={<Lock className="h-3 w-3" />}
          disabled={busy || agent.state === "jailed" || agent.state === "revoked"}
          onClick={() => jail.mutate()}
        >
          Jail
        </AgentBtn>
        <AgentBtn
          variant="neutral"
          icon={<Unlock className="h-3 w-3" />}
          disabled={busy || agent.state !== "jailed"}
          onClick={() => release.mutate()}
        >
          Release
        </AgentBtn>
        <AgentBtn
          variant="wanted"
          icon={<Ban className="h-3 w-3" />}
          disabled={busy || agent.state === "revoked"}
          onClick={() => revoke.mutate()}
        >
          Revoke
        </AgentBtn>
      </div>
    </article>
  );
}

function DeputyBadge({ label, state }: { label: string; state: AgentState }) {
  const initials = label
    .split(/[\s_-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .join("") || "?";

  const ring =
    state === "revoked"
      ? "border-wanted-red/60 text-wanted-red"
      : state === "jailed"
        ? "border-approval-amber text-brass-dark"
        : state === "idle"
          ? "border-ink/30 text-ink-soft"
          : "border-brass-dark text-brass-dark";

  return (
    <div
      className={cn(
        "flex h-11 w-11 flex-shrink-0 items-center justify-center border-2 bg-parchment-deep/60 font-heading text-base",
        ring,
      )}
      aria-hidden
    >
      {initials}
    </div>
  );
}

function StateBadge({ state }: { state: AgentState }) {
  const classes =
    state === "active"
      ? "border-brass-dark text-brass-dark bg-brass-light/20"
      : state === "jailed"
        ? "border-approval-amber text-brass-dark bg-approval-amber/20"
        : state === "revoked"
          ? "border-wanted-red text-wanted-red bg-wanted-red/10"
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
      <div className={cn("mt-0.5 truncate text-sm", color)}>{value}</div>
    </div>
  );
}

function AgentBtn({
  variant,
  icon,
  children,
  ...rest
}: {
  variant: "neutral" | "wanted";
  icon?: React.ReactNode;
  children: React.ReactNode;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children">) {
  const base =
    "flex items-center justify-center gap-1.5 bg-parchment px-2 py-2 font-mono text-[10px] uppercase tracking-widest transition disabled:cursor-not-allowed disabled:opacity-40";
  const variantClass =
    variant === "wanted"
      ? "text-wanted-red hover:bg-wanted-red/10"
      : "text-ink hover:bg-brass-light/20";
  return (
    <button type="button" {...rest} className={cn(base, variantClass, rest.className)}>
      {icon}
      <span>{children}</span>
    </button>
  );
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
