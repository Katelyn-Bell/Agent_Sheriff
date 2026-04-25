"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getEval, getEvalResults } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store";
import type {
  Decision,
  DisagreementCategory,
  EvalResultDTO,
  EvalRunDTO,
} from "@/lib/types";
import { cn } from "@/lib/utils";

export default function TrialRecordDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const streamedRun = useAppStore((s) => s.evals[id]);

  const runQuery = useQuery<EvalRunDTO>({
    queryKey: ["eval", id],
    queryFn: () => getEval(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status?.toLowerCase();
      return status === "running" || status === "queued" ? 2000 : false;
    },
  });

  const resultsQuery = useQuery<EvalResultDTO[]>({
    queryKey: ["eval-results", id],
    queryFn: () => getEvalResults(id),
  });

  const run = runQuery.data ?? streamedRun;
  const results = resultsQuery.data ?? [];

  return (
    <section>
      <PageHeader
        title={`Trial Record ${id}`}
        subtitle={
          run
            ? `${run.policy_version_id} · status ${run.status}`
            : "Loading…"
        }
        actions={
          <Link
            href="/evals"
            className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
          >
            ← Back to runs
          </Link>
        }
      />

      {!run && (runQuery.isLoading ? (
        <p className="text-sm text-ink-soft">Fetching run metadata…</p>
      ) : runQuery.isError ? (
        <ErrorBlock error={runQuery.error} />
      ) : (
        <p className="text-sm text-ink-soft">No data yet.</p>
      ))}

      {run && <RunSummary run={run} />}

      {results.length > 0 && (
        <>
          <h2 className="mt-8 mb-3 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
            Row-level results
          </h2>
          <ol className="space-y-2">
            {results.map((r) => (
              <ResultRow key={r.id} result={r} />
            ))}
          </ol>
        </>
      )}

      {resultsQuery.isError && <ErrorBlock error={resultsQuery.error} />}
    </section>
  );
}

function RunSummary({ run }: { run: EvalRunDTO }) {
  const total = run.agreed + run.disagreed + run.errored;
  const agreement = total > 0 ? Math.round((run.agreed / total) * 100) : 0;
  const pct =
    run.total_entries > 0
      ? Math.round((run.processed_entries / run.total_entries) * 100)
      : 0;

  return (
    <div className="grid gap-4 md:grid-cols-[1fr_auto]">
      <div className="border border-brass/40 bg-parchment-deep/40 p-4">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
          Progress
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-ink/15">
          <div
            className="h-full bg-brass-dark transition-[width]"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-2 font-mono text-xs text-ink-soft">
          {run.processed_entries} / {run.total_entries} processed
        </p>
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <Stat label="Agreed" value={run.agreed} accent="brass" />
          <Stat label="Disagreed" value={run.disagreed} accent="wanted" />
          <Stat label="Errored" value={run.errored} accent="amber" />
        </div>
      </div>
      <div className="border border-brass/40 bg-parchment-deep/40 p-4 md:min-w-[180px]">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
          Agreement
        </div>
        <p className="font-heading text-5xl leading-none text-ink">
          {agreement}%
        </p>
        <p className="mt-2 font-mono text-[10px] text-ink-soft">
          created {formatTime(run.created_at)}
          {run.completed_at ? ` · done ${formatTime(run.completed_at)}` : ""}
        </p>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "wanted" | "amber" | "brass";
}) {
  const color =
    accent === "wanted"
      ? "text-wanted-red"
      : accent === "amber"
        ? "text-approval-amber"
        : "text-brass-dark";
  return (
    <div>
      <p className={cn("font-heading text-2xl", color)}>{value}</p>
      <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </p>
    </div>
  );
}

function ResultRow({ result }: { result: EvalResultDTO }) {
  const [expanded, setExpanded] = useState(false);
  const disagreementColor = disagreementCategoryColor(
    result.disagreement_category,
  );
  return (
    <li
      className={cn(
        "border border-brass/30 bg-parchment transition",
        !result.agreement && "border-wanted-red/50",
        expanded && "bg-parchment-deep/40",
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="grid w-full grid-cols-[1fr_auto_auto_auto] items-center gap-4 px-3 py-2 text-left"
      >
        <span className="font-mono text-[11px] text-ink-soft">
          {result.audit_id}
        </span>
        <DecisionArrow
          from={result.original_decision}
          to={result.replayed_decision}
        />
        {result.disagreement_category && (
          <span
            className={cn(
              "font-mono text-[10px] uppercase tracking-widest",
              disagreementColor,
            )}
          >
            {result.disagreement_category}
          </span>
        )}
        {result.agreement ? (
          <span className="font-mono text-[10px] uppercase tracking-widest text-brass-dark">
            agreed
          </span>
        ) : (
          <span className="font-mono text-[10px] uppercase tracking-widest text-wanted-red">
            disagreed
          </span>
        )}
      </button>
      {expanded && (
        <div className="space-y-3 border-t border-brass/20 bg-parchment px-3 py-3 text-sm">
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
              Replay reason
            </div>
            <p className="text-ink">{result.replay_reason}</p>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <Meta
              label="Matched rule"
              value={result.matched_rule_id ?? "—"}
            />
            <Meta
              label="Judge"
              value={result.judge_used ? "used" : "skipped"}
            />
            <Meta label="Audit id" value={result.audit_id} />
          </div>
        </div>
      )}
    </li>
  );
}

function DecisionArrow({ from, to }: { from: Decision; to: Decision }) {
  return (
    <span className="flex items-baseline gap-2 font-mono text-[10px] uppercase tracking-widest">
      <span className={decisionColor(from)}>{from}</span>
      <span className="text-ink-soft">→</span>
      <span className={decisionColor(to)}>{to}</span>
    </span>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-ink-soft">
        {label}
      </div>
      <div className="font-mono text-xs text-ink">{value}</div>
    </div>
  );
}

function ErrorBlock({ error }: { error: unknown }) {
  return (
    <div className="border-l-4 border-wanted-red bg-parchment-deep/60 p-4">
      <p className="font-heading text-base text-wanted-red">
        Couldn&apos;t load
      </p>
      <p className="mt-1 text-sm text-ink-soft">
        {error instanceof Error ? error.message : "Unknown error"}
      </p>
    </div>
  );
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

function disagreementCategoryColor(
  category: DisagreementCategory | undefined,
): string {
  switch (category) {
    case "more_permissive":
      return "text-approval-amber";
    case "more_restrictive":
      return "text-brass-dark";
    case "reason_changed":
      return "text-ink-soft";
    case "approval_vs_direct":
      return "text-approval-amber";
    case "error":
      return "text-wanted-red";
    default:
      return "text-ink-soft";
  }
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toISOString().replace("T", " ").slice(0, 19);
}
