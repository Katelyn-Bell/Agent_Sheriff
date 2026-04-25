"use client";

import { useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/PageHeader";
import {
  API_BASE_URL,
  runDemoScenario,
  type DemoScenario,
} from "@/lib/api";
import {
  selectEvalsList,
  selectKpis,
  useAppStore,
} from "@/lib/store";
import type { AuditEntryDTO, Decision } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function TownOverviewPage() {
  return (
    <section>
      <PageHeader
        title="Town Overview"
        subtitle="Live activity · policy · evals"
      />
      <KpiRow />
      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <RecentActivity />
        <aside className="space-y-6">
          <DemoLauncher />
          <PublishedPolicyCard />
          <LatestEvalCard />
        </aside>
      </div>
    </section>
  );
}

function KpiRow() {
  const kpis = useAppStore(selectKpis);
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Kpi label="Allowed" value={kpis.allowed} accent="ink" />
      <Kpi label="Denied" value={kpis.denied} accent="wanted" />
      <Kpi label="Awaiting approval" value={kpis.awaiting} accent="amber" />
      <Kpi
        label="Active policy"
        value={kpis.activePolicyName ?? "—"}
        accent="ink"
        small={kpis.activePolicyName !== null}
      />
    </div>
  );
}

function Kpi({
  label,
  value,
  accent,
  small,
}: {
  label: string;
  value: string | number;
  accent: "ink" | "wanted" | "amber";
  small?: boolean;
}) {
  const color =
    accent === "wanted"
      ? "text-wanted-red"
      : accent === "amber"
        ? "text-approval-amber"
        : "text-ink";
  return (
    <div className="border border-brass/40 bg-parchment-deep/50 p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
        {label}
      </div>
      <div
        className={cn(
          "mt-2 font-heading leading-none",
          small ? "text-xl" : "text-3xl",
          color,
        )}
      >
        {value}
      </div>
    </div>
  );
}

function RecentActivity() {
  const audit = useAppStore((s) => s.audit);
  const recent = audit.slice(0, 12);
  return (
    <Panel title="Recent activity">
      {recent.length === 0 ? (
        <p className="text-sm text-ink-soft">
          No activity yet. Kick off a demo scenario or wait for agents.
        </p>
      ) : (
        <ol className="divide-y divide-brass/20">
          {recent.map((entry) => (
            <AuditRow key={entry.id} entry={entry} />
          ))}
        </ol>
      )}
    </Panel>
  );
}

function AuditRow({ entry }: { entry: AuditEntryDTO }) {
  return (
    <li className="py-2.5 first:pt-0 last:pb-0">
      <div className="flex items-baseline gap-3 font-mono text-[11px]">
        <span className="text-ink-soft">{formatTime(entry.created_at)}</span>
        <span className="text-ink">{entry.agent_label ?? entry.agent_id}</span>
        <span className="text-ink-soft">→</span>
        <span className="text-ink">{entry.tool}</span>
        <span
          className={cn(
            "ml-auto uppercase tracking-[0.22em]",
            decisionColor(entry.decision),
          )}
        >
          {entry.decision}
        </span>
      </div>
      {entry.reason && (
        <p className="mt-0.5 pl-[4.5rem] text-xs text-ink-soft">
          {entry.reason}
        </p>
      )}
    </li>
  );
}

function DemoLauncher() {
  const mutation = useMutation({
    mutationFn: (scenario: DemoScenario) => runDemoScenario(scenario),
  });
  return (
    <Panel title="Run a demo scenario">
      <div className="flex flex-col gap-2">
        <DemoButton
          label="Run Good"
          hint="Allowed workflow"
          variant="neutral"
          onClick={() => mutation.mutate("good")}
          pending={mutation.isPending && mutation.variables === "good"}
        />
        <DemoButton
          label="Run Injection"
          hint="Exfiltration → deny"
          variant="wanted"
          onClick={() => mutation.mutate("injection")}
          pending={mutation.isPending && mutation.variables === "injection"}
        />
        <DemoButton
          label="Run Approval"
          hint="Human-in-the-loop"
          variant="amber"
          onClick={() => mutation.mutate("approval")}
          pending={mutation.isPending && mutation.variables === "approval"}
        />
      </div>
      {mutation.isError && (
        <p className="mt-3 font-mono text-[10px] uppercase tracking-widest text-wanted-red">
          Backend offline · check {API_BASE_URL}
        </p>
      )}
    </Panel>
  );
}

function DemoButton({
  label,
  hint,
  variant,
  onClick,
  pending,
}: {
  label: string;
  hint: string;
  variant: "neutral" | "wanted" | "amber";
  onClick: () => void;
  pending: boolean;
}) {
  const classes =
    variant === "wanted"
      ? "border-wanted-red text-wanted-red hover:bg-wanted-red/10"
      : variant === "amber"
        ? "border-brass-dark bg-approval-amber/70 text-ink hover:bg-approval-amber"
        : "border-ink text-ink hover:bg-ink/5";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={pending}
      className={cn(
        "flex items-center justify-between border px-3 py-2 text-left transition disabled:opacity-50",
        classes,
      )}
    >
      <span className="font-heading text-sm">{label}</span>
      <span className="font-mono text-[10px] uppercase tracking-widest opacity-70">
        {pending ? "running…" : hint}
      </span>
    </button>
  );
}

function PublishedPolicyCard() {
  const latestPolicy = useAppStore((s) => s.latestPolicy);
  return (
    <Panel title="Currently published">
      {latestPolicy ? (
        <>
          <p className="font-heading text-base text-ink">{latestPolicy.name}</p>
          <p className="mt-1 font-mono text-xs text-ink-soft">
            v{latestPolicy.version} · {latestPolicy.static_rules.length} rules
          </p>
          <p className="mt-3 line-clamp-3 text-xs text-ink-soft">
            {latestPolicy.intent_summary}
          </p>
        </>
      ) : (
        <p className="text-sm text-ink-soft">No published version yet.</p>
      )}
    </Panel>
  );
}

function LatestEvalCard() {
  const evals = useAppStore(selectEvalsList);
  const latest = evals[0];
  return (
    <Panel title="Latest eval">
      {latest ? (
        <>
          <p className="font-mono text-xs text-ink">{latest.id}</p>
          <p className="mt-1 font-mono text-xs text-ink-soft">
            status:{" "}
            <strong className="text-ink">{latest.status}</strong>
          </p>
          <p className="mt-1 font-mono text-xs text-ink-soft">
            {latest.processed_entries} / {latest.total_entries} processed
          </p>
          <p className="mt-1 font-mono text-xs text-ink-soft">
            {latest.disagreed} disagreements · {latest.errored} errors
          </p>
        </>
      ) : (
        <p className="text-sm text-ink-soft">No eval runs yet.</p>
      )}
    </Panel>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-brass/40 bg-parchment-deep/40 p-4">
      <div className="mb-3 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
        {title}
      </div>
      {children}
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "--:--:--";
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  const ss = String(d.getUTCSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function decisionColor(decision: Decision): string {
  switch (decision) {
    case "allow":
      return "text-brass-dark";
    case "deny":
      return "text-wanted-red";
    case "approval_required":
      return "text-approval-amber";
  }
}
