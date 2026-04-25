"use client";

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store";
import type { AuditEntryDTO, Decision } from "@/lib/types";
import { cn } from "@/lib/utils";

type DecisionFilter = Decision | "all";

export default function LedgerPage() {
  const audit = useAppStore((s) => s.audit);

  const [decision, setDecision] = useState<DecisionFilter>("all");
  const [agentId, setAgentId] = useState("all");
  const [policyId, setPolicyId] = useState("all");
  const [search, setSearch] = useState("");

  const agentOptions = useMemo(
    () =>
      Array.from(new Set(audit.map((e) => e.agent_id))).sort((a, b) =>
        a.localeCompare(b),
      ),
    [audit],
  );
  const policyOptions = useMemo(
    () =>
      Array.from(new Set(audit.map((e) => e.policy_version_id))).sort((a, b) =>
        a.localeCompare(b),
      ),
    [audit],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return audit.filter((e) => {
      if (decision !== "all" && e.decision !== decision) return false;
      if (agentId !== "all" && e.agent_id !== agentId) return false;
      if (policyId !== "all" && e.policy_version_id !== policyId) return false;
      if (q && !e.tool.toLowerCase().includes(q) && !e.reason.toLowerCase().includes(q)) {
        return false;
      }
      return true;
    });
  }, [audit, decision, agentId, policyId, search]);

  return (
    <section>
      <PageHeader
        title="Sheriff's Ledger"
        subtitle={`${filtered.length} of ${audit.length} entries`}
      />

      <div className="mb-6 grid gap-3 rounded-sm border border-brass/40 bg-parchment-deep/40 p-4 md:grid-cols-4">
        <FilterSelect
          label="Decision"
          value={decision}
          onChange={(v) => setDecision(v as DecisionFilter)}
          options={[
            { value: "all", label: "All decisions" },
            { value: "allow", label: "Allow" },
            { value: "deny", label: "Deny" },
            { value: "approval_required", label: "Approval required" },
          ]}
        />
        <FilterSelect
          label="Agent"
          value={agentId}
          onChange={setAgentId}
          options={[
            { value: "all", label: "All agents" },
            ...agentOptions.map((a) => ({ value: a, label: a })),
          ]}
        />
        <FilterSelect
          label="Policy version"
          value={policyId}
          onChange={setPolicyId}
          options={[
            { value: "all", label: "All policies" },
            ...policyOptions.map((p) => ({ value: p, label: p })),
          ]}
        />
        <FilterInput
          label="Search tool / reason"
          value={search}
          onChange={setSearch}
          placeholder="gmail.send_email, exfil, …"
        />
      </div>

      {audit.length === 0 ? (
        <EmptyState />
      ) : filtered.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-8 text-center">
          <p className="font-heading text-lg text-ink">No matches</p>
          <p className="mt-1 text-sm text-ink-soft">
            Adjust the filters above or clear them to see all entries.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-sm border border-brass/40">
          <ol className="divide-y divide-brass/20">
            {filtered.map((entry) => (
              <LedgerRow key={entry.id} entry={entry} />
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

function LedgerRow({ entry }: { entry: AuditEntryDTO }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li
      className={cn(
        "bg-parchment transition hover:bg-parchment-deep/40",
        expanded && "bg-parchment-deep/40",
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-baseline gap-3 px-4 py-2.5 text-left"
      >
        <span className="font-mono text-[11px] text-ink-soft">
          {formatTime(entry.created_at)}
        </span>
        <span className="font-mono text-[11px] text-ink">
          {entry.agent_label ?? entry.agent_id}
        </span>
        <span className="font-mono text-[11px] text-ink">{entry.tool}</span>
        <span
          className={cn(
            "ml-auto font-mono text-[10px] uppercase tracking-[0.22em]",
            decisionColor(entry.decision),
          )}
        >
          {entry.decision}
        </span>
        <span className="font-mono text-[10px] text-ink-soft">
          {expanded ? "▾" : "▸"}
        </span>
      </button>
      {expanded && <LedgerDetail entry={entry} />}
    </li>
  );
}

function LedgerDetail({ entry }: { entry: AuditEntryDTO }) {
  return (
    <div className="space-y-4 border-t border-brass/20 bg-parchment px-4 py-4 text-sm">
      <DetailRow label="Reason" value={entry.reason} />
      {entry.user_explanation && (
        <DetailRow label="User explanation" value={entry.user_explanation} />
      )}
      <div className="grid gap-4 md:grid-cols-2">
        <DetailCode label="Args" value={entry.args} />
        <DetailCode label="Context" value={entry.context} />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Meta label="Policy" value={entry.policy_version_id} />
        <Meta label="Rule" value={entry.matched_rule_id ?? "—"} />
        <Meta
          label="Judge"
          value={entry.judge_used ? "used" : "skipped"}
          accent={entry.judge_used ? "brass" : undefined}
        />
        <Meta label="Risk" value={String(entry.risk_score)} accent="brass" />
        <Meta
          label="Approval"
          value={entry.approval_state ?? "—"}
          accent={entry.approval_state === "approved" ? "amber" : undefined}
        />
        <Meta
          label="Signals"
          value={entry.heuristic_signals.join(", ") || "none"}
        />
      </div>
      {entry.judge_rationale && (
        <div>
          <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
            Judge rationale
          </div>
          <p className="whitespace-pre-wrap rounded-sm border border-ink/20 bg-parchment-deep/60 p-3 text-xs text-ink">
            {entry.judge_rationale}
          </p>
        </div>
      )}
      {entry.execution_result && (
        <DetailCode
          label="Execution result"
          value={entry.execution_result}
        />
      )}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <p className="text-sm text-ink">{value}</p>
    </div>
  );
}

function DetailCode({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <pre className="max-h-48 overflow-auto rounded-sm border border-ink/20 bg-parchment-deep/60 p-2 font-mono text-[11px] leading-relaxed text-ink">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function Meta({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
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
      <div className="font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <div className={cn("font-mono text-xs", color)}>{value}</div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-ink/40 bg-parchment px-2 py-1.5 text-sm text-ink focus:border-brass focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border border-ink/40 bg-parchment px-2 py-1.5 text-sm text-ink placeholder:text-ink-soft/60 focus:border-brass focus:outline-none"
      />
    </label>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
      <p className="font-heading text-xl text-ink">Ledger is clean</p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
        Every tool call through the gateway lands here. Run a demo scenario
        from the Town Overview to seed the first entries.
      </p>
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
