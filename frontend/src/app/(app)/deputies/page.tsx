"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useShallow } from "zustand/shallow";
import {
  Activity,
  Ban,
  Clock3,
  Filter,
  Lock,
  RotateCw,
  ShieldCheck,
  Unlock,
  UsersRound,
} from "lucide-react";
import { jailAgent, listAgents, releaseAgent, revokeAgent } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { selectAgentsList, useAppStore } from "@/lib/store";
import type {
  AgentState,
  AgentStateDTO,
  AuditEntryDTO,
  Decision,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type StateFilter = AgentState | "all";

const AGENT_QUERY_KEY = ["agents"] as const;

const FILTERS: { value: StateFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "jailed", label: "Jailed" },
  { value: "revoked", label: "Revoked" },
  { value: "idle", label: "Idle" },
];

export default function DeputiesPage() {
  const rehydrate = useAppStore((s) => s.rehydrate);
  const agents = useAppStore(useShallow(selectAgentsList));
  const audit = useAppStore((s) => s.audit);
  const [filter, setFilter] = useState<StateFilter>("all");

  const agentsQuery = useQuery({
    queryKey: AGENT_QUERY_KEY,
    queryFn: ({ signal }) => listAgents(signal),
  });

  useEffect(() => {
    if (agentsQuery.data) rehydrate({ agents: agentsQuery.data });
  }, [agentsQuery.data, rehydrate]);

  const roster = useMemo(() => enrichAgents(agents, audit), [agents, audit]);
  const visibleAgents = useMemo(
    () =>
      roster.filter((agent) => filter === "all" || agent.state === filter),
    [roster, filter],
  );
  const counts = useMemo(() => summarizeAgents(roster), [roster]);

  return (
    <section>
      <PageHeader
        title="Deputies"
        subtitle={
          roster.length === 0
            ? "No agents on the roster"
            : `${roster.length} agent${roster.length === 1 ? "" : "s"} on the roster`
        }
        actions={
          <button
            type="button"
            onClick={() => void agentsQuery.refetch()}
            disabled={agentsQuery.isFetching}
            className="inline-flex items-center gap-2 border border-brass/50 bg-parchment-deep/50 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-ink transition hover:bg-brass-light/20 disabled:cursor-not-allowed disabled:opacity-50"
            title="Refresh roster"
          >
            <RotateCw
              className={cn("h-3.5 w-3.5", agentsQuery.isFetching && "animate-spin")}
            />
            Refresh
          </button>
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <SummaryTile
          icon={<UsersRound className="h-4 w-4" />}
          label="Roster"
          value={roster.length}
        />
        <SummaryTile
          icon={<Activity className="h-4 w-4" />}
          label="Active"
          value={counts.active}
          accent="brass"
        />
        <SummaryTile
          icon={<Lock className="h-4 w-4" />}
          label="Jailed"
          value={counts.jailed}
          accent={counts.jailed > 0 ? "amber" : undefined}
        />
        <SummaryTile
          icon={<Ban className="h-4 w-4" />}
          label="Revoked"
          value={counts.revoked}
          accent={counts.revoked > 0 ? "wanted" : undefined}
        />
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2 border border-brass/40 bg-parchment-deep/40 p-3">
        <div className="mr-1 inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
          <Filter className="h-3.5 w-3.5" />
          State
        </div>
        {FILTERS.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => setFilter(item.value)}
            className={cn(
              "border px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] transition",
              filter === item.value
                ? "border-wanted-red bg-parchment text-wanted-red"
                : "border-brass/40 text-ink-soft hover:border-brass hover:text-ink",
            )}
          >
            {item.label}
            <span className="ml-2 text-ink-soft">
              {item.value === "all" ? roster.length : counts[item.value]}
            </span>
          </button>
        ))}
      </div>

      {agentsQuery.isError && (
        <div className="mb-6 border border-wanted-red/40 bg-wanted-red/10 px-4 py-3 font-mono text-[11px] uppercase tracking-[0.16em] text-wanted-red">
          Roster refresh failed. Showing the latest local stream state.
        </div>
      )}

      {roster.length === 0 ? (
        <EmptyRoster />
      ) : visibleAgents.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-8 text-center">
          <p className="font-heading text-lg text-ink">No deputies in this state</p>
          <p className="mt-1 text-sm text-ink-soft">
            Change the state filter to see the rest of the roster.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {visibleAgents.map((agent) => (
            <DeputyCard key={agent.agent_id} agent={agent} />
          ))}
        </div>
      )}
    </section>
  );
}

function EmptyRoster() {
  return (
    <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
      <ShieldCheck className="mx-auto h-8 w-8 text-brass-dark/70" />
      <p className="mt-3 font-heading text-xl text-ink">No deputies reporting</p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
        Agents appear here once they hit the gateway. Kick off a demo scenario
        to seed the roster.
      </p>
    </div>
  );
}

function DeputyCard({ agent }: { agent: AgentStateDTO }) {
  const queryClient = useQueryClient();
  const pushAgent = (updated: AgentStateDTO) => {
    const merged = preserveActivity(agent, updated);
    useAppStore.getState().applyFrame({ type: "agent_state", payload: merged });
    queryClient.setQueryData<AgentStateDTO[]>(AGENT_QUERY_KEY, (old) =>
      upsertAgent(old, merged),
    );
  };

  const jail = useMutation({
    mutationFn: () => jailAgent(agent.agent_id),
    onSuccess: pushAgent,
  });
  const release = useMutation({
    mutationFn: () => releaseAgent(agent.agent_id),
    onSuccess: pushAgent,
  });
  const revoke = useMutation({
    mutationFn: () => revokeAgent(agent.agent_id),
    onSuccess: pushAgent,
  });

  const busy = jail.isPending || release.isPending || revoke.isPending;
  const label = agent.agent_label ?? agent.agent_id;
  const isFresh = agent.request_count === 0 && !agent.last_seen_at;
  const error = jail.error ?? release.error ?? revoke.error;

  return (
    <article
      className={cn(
        "flex min-h-[320px] flex-col overflow-hidden border bg-parchment transition hover:-translate-y-0.5 hover:shadow-[0_10px_24px_rgba(43,24,16,0.14)]",
        cardBorder(agent.state),
      )}
    >
      <header className="border-b border-brass/25 bg-parchment-deep/45 px-4 py-4">
        <div className="flex items-start gap-3">
          <DeputyBadge label={label} state={agent.state} />
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-start gap-2">
              <p className="min-w-0 flex-1 truncate font-heading text-xl leading-none text-ink">
                {label}
              </p>
              <StateBadge state={agent.state} />
            </div>
            <p className="mt-1 truncate font-mono text-[10px] text-ink-soft">
              {agent.agent_id}
            </p>
          </div>
        </div>
      </header>

      {isFresh ? (
        <div className="flex flex-1 flex-col items-center justify-center px-5 py-8 text-center">
          <ShieldCheck className="h-8 w-8 text-brass-dark/65" />
          <p className="mt-3 font-heading text-base text-ink">
            Sworn in, not on duty
          </p>
          <p className="mt-1 max-w-[30ch] text-xs leading-relaxed text-ink-soft">
            Awaiting first request. Stats appear once this deputy starts
            calling tools.
          </p>
        </div>
      ) : (
        <div className="flex-1 px-4 py-4">
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Requests" value={agent.request_count} />
            <Stat
              label="Blocked"
              value={agent.blocked_count}
              accent={agent.blocked_count > 0 ? "wanted" : undefined}
            />
            <Stat
              label="Last decision"
              value={formatDecision(agent.last_decision)}
              accent={
                agent.last_decision ? decisionAccent(agent.last_decision) : undefined
              }
            />
            <Stat
              label="Last seen"
              value={formatRelative(agent.last_seen_at)}
              icon={<Clock3 className="h-3 w-3" />}
            />
          </div>

          {agent.active_policy_version_id && (
            <div className="mt-4 border-t border-brass/20 pt-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-soft">
                Policy
              </div>
              <p className="mt-1 truncate font-mono text-xs text-ink">
                {agent.active_policy_version_id}
              </p>
            </div>
          )}
        </div>
      )}

      {error && (
        <p className="mx-4 mb-3 border border-wanted-red/30 bg-wanted-red/10 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-wanted-red">
          Action failed
        </p>
      )}

      <div className="grid grid-cols-3 gap-px border-t border-brass/30 bg-brass/30">
        <AgentBtn
          variant="neutral"
          icon={<Lock className="h-3.5 w-3.5" />}
          disabled={busy || agent.state === "jailed" || agent.state === "revoked"}
          onClick={() => jail.mutate()}
          title="Jail deputy"
        >
          {jail.isPending ? "Jailing" : "Jail"}
        </AgentBtn>
        <AgentBtn
          variant="neutral"
          icon={<Unlock className="h-3.5 w-3.5" />}
          disabled={busy || agent.state !== "jailed"}
          onClick={() => release.mutate()}
          title="Release deputy"
        >
          {release.isPending ? "Opening" : "Release"}
        </AgentBtn>
        <AgentBtn
          variant="wanted"
          icon={<Ban className="h-3.5 w-3.5" />}
          disabled={busy || agent.state === "revoked"}
          onClick={() => revoke.mutate()}
          title="Revoke deputy"
        >
          {revoke.isPending ? "Revoking" : "Revoke"}
        </AgentBtn>
      </div>
    </article>
  );
}

function SummaryTile({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
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
    <div className="border border-brass/40 bg-parchment-deep/50 p-4">
      <div className="flex items-center justify-between text-ink-soft">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em]">
          {label}
        </span>
        {icon}
      </div>
      <div className={cn("mt-3 font-heading text-3xl leading-none", color)}>
        {value}
      </div>
    </div>
  );
}

function DeputyBadge({ label, state }: { label: string; state: AgentState }) {
  const initials =
    label
      .split(/[\s_-]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s[0]?.toUpperCase() ?? "")
      .join("") || "?";

  const ring =
    state === "revoked"
      ? "border-wanted-red/70 text-wanted-red"
      : state === "jailed"
        ? "border-approval-amber text-brass-dark"
        : state === "idle"
          ? "border-ink/25 text-ink-soft"
          : "border-brass-dark text-brass-dark";

  return (
    <div
      className={cn(
        "flex h-12 w-12 flex-shrink-0 items-center justify-center border-2 bg-parchment font-heading text-base",
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
          : "border-ink-soft/50 text-ink-soft bg-parchment-deep/40";
  return (
    <span
      className={cn(
        "shrink-0 border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em]",
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
  icon,
}: {
  label: string;
  value: string | number;
  accent?: "wanted" | "amber" | "brass";
  icon?: React.ReactNode;
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
    <div className="min-w-0 border border-brass/25 bg-parchment-deep/35 px-3 py-2">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.16em] text-ink-soft">
        {icon}
        <span className="truncate">{label}</span>
      </div>
      <div className={cn("mt-1 truncate font-mono text-sm", color)}>{value}</div>
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
    "flex min-h-11 items-center justify-center gap-1.5 bg-parchment px-2 py-2 font-mono text-[10px] uppercase tracking-[0.14em] transition disabled:cursor-not-allowed disabled:opacity-40";
  const variantClass =
    variant === "wanted"
      ? "text-wanted-red hover:bg-wanted-red/10"
      : "text-ink hover:bg-brass-light/20";
  return (
    <button type="button" {...rest} className={cn(base, variantClass, rest.className)}>
      {icon}
      <span className="truncate">{children}</span>
    </button>
  );
}

function enrichAgents(
  agents: AgentStateDTO[],
  audit: AuditEntryDTO[],
): AgentStateDTO[] {
  const activity = new Map<
    string,
    {
      requests: number;
      blocked: number;
      latest: AuditEntryDTO | null;
    }
  >();

  for (const entry of audit) {
    const current =
      activity.get(entry.agent_id) ?? { requests: 0, blocked: 0, latest: null };
    current.requests += 1;
    if (entry.decision === "deny") current.blocked += 1;
    if (
      !current.latest ||
      new Date(entry.ts).getTime() > new Date(current.latest.ts).getTime()
    ) {
      current.latest = entry;
    }
    activity.set(entry.agent_id, current);
  }

  return agents.map((agent) => {
    const agentActivity = activity.get(agent.agent_id);
    const latest = agentActivity?.latest;
    return {
      ...agent,
      request_count: Math.max(agent.request_count, agentActivity?.requests ?? 0),
      blocked_count: Math.max(agent.blocked_count, agentActivity?.blocked ?? 0),
      last_decision: agent.last_decision ?? latest?.decision ?? null,
      last_seen_at: agent.last_seen_at ?? latest?.ts ?? null,
      active_policy_version_id:
        agent.active_policy_version_id ?? latest?.policy_version_id ?? null,
    };
  });
}

function summarizeAgents(agents: AgentStateDTO[]) {
  return agents.reduce(
    (acc, agent) => {
      acc[agent.state] += 1;
      return acc;
    },
    { active: 0, idle: 0, jailed: 0, revoked: 0 } satisfies Record<AgentState, number>,
  );
}

function upsertAgent(
  agents: AgentStateDTO[] | undefined,
  updated: AgentStateDTO,
): AgentStateDTO[] {
  if (!agents) return [updated];
  const found = agents.some((agent) => agent.agent_id === updated.agent_id);
  const next = found
    ? agents.map((agent) =>
        agent.agent_id === updated.agent_id ? { ...agent, ...updated } : agent,
      )
    : [...agents, updated];
  return next.sort((a, b) =>
    (a.agent_label ?? a.agent_id).localeCompare(b.agent_label ?? b.agent_id),
  );
}

function preserveActivity(
  previous: AgentStateDTO,
  updated: AgentStateDTO,
): AgentStateDTO {
  return {
    ...previous,
    ...updated,
    agent_label: updated.agent_label ?? previous.agent_label,
    request_count: Math.max(previous.request_count, updated.request_count),
    blocked_count: Math.max(previous.blocked_count, updated.blocked_count),
    active_policy_version_id:
      updated.active_policy_version_id ?? previous.active_policy_version_id,
    last_decision: updated.last_decision ?? previous.last_decision,
    last_seen_at: updated.last_seen_at ?? previous.last_seen_at,
  };
}

function cardBorder(state: AgentState) {
  switch (state) {
    case "revoked":
      return "border-wanted-red/55";
    case "jailed":
      return "border-approval-amber/70";
    case "active":
      return "border-brass/60";
    case "idle":
      return "border-ink/20";
  }
}

function decisionAccent(decision: Decision): "wanted" | "amber" | "brass" {
  return decision === "deny"
    ? "wanted"
    : decision === "approval_required"
      ? "amber"
      : "brass";
}

function formatDecision(decision: Decision | null): string {
  return decision ? decision.replace("_", " ") : "--";
}

function formatRelative(iso: string | null): string {
  if (!iso) return "--";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "--";
  const diff = Date.now() - then;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}
