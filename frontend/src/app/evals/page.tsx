"use client";

import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { useShallow } from "zustand/shallow";
import { createEval } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { selectEvalsList, useAppStore } from "@/lib/store";
import type { EvalRunDTO } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function TrialRecordsPage() {
  const evals = useAppStore(useShallow(selectEvalsList));
  const latestPolicy = useAppStore((s) => s.latestPolicy);

  const mutation = useMutation({
    mutationFn: (policy_version_id: string) => createEval(policy_version_id),
  });

  const canRun = !!latestPolicy && !mutation.isPending;

  return (
    <section>
      <PageHeader
        title="Trial Records"
        subtitle={
          evals.length === 0
            ? "No runs yet"
            : `${evals.length} run${evals.length === 1 ? "" : "s"}`
        }
        actions={
          <button
            type="button"
            onClick={() => latestPolicy && mutation.mutate(latestPolicy.id)}
            disabled={!canRun}
            className="border border-ink bg-brass-dark px-4 py-2 text-sm font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Starting…" : "New eval run"}
          </button>
        }
      />

      {!latestPolicy && (
        <div className="mb-6 border-l-4 border-approval-amber bg-parchment-deep/60 p-4 text-sm text-ink">
          Publish a policy first.{" "}
          <Link href="/laws" className="underline underline-offset-2">
            Open Town Laws →
          </Link>
        </div>
      )}

      {mutation.isError && (
        <div className="mb-6 border-l-4 border-wanted-red bg-parchment-deep/60 p-4 text-sm text-ink">
          <p className="font-heading text-base text-wanted-red">
            Couldn&apos;t start the run
          </p>
          <p className="mt-1 text-ink-soft">
            {mutation.error instanceof Error
              ? mutation.error.message
              : "Unknown error"}
          </p>
        </div>
      )}

      {evals.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
          <p className="font-heading text-xl text-ink">No runs on the docket</p>
          <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
            An eval replays historical ledger entries against a draft policy so
            you can see what would change before you publish.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-sm border border-brass/40">
          <div className="grid grid-cols-[1fr_140px_1fr_auto] gap-4 border-b border-brass/40 bg-parchment-deep/60 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
            <span>Run</span>
            <span>Status</span>
            <span>Progress</span>
            <span>Agreement</span>
          </div>
          <ol className="divide-y divide-brass/20">
            {evals.map((run) => (
              <EvalRow key={run.id} run={run} />
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

function EvalRow({ run }: { run: EvalRunDTO }) {
  const pct =
    run.total_entries > 0
      ? Math.round((run.processed_entries / run.total_entries) * 100)
      : 0;
  const total = run.agreed + run.disagreed + run.errored;
  const agreement = total > 0 ? Math.round((run.agreed / total) * 100) : 0;

  return (
    <li>
      <Link
        href={`/evals/${run.id}`}
        className="grid grid-cols-[1fr_140px_1fr_auto] items-center gap-4 bg-parchment px-4 py-3 transition hover:bg-parchment-deep/40"
      >
        <div>
          <p className="font-mono text-xs text-ink">{run.id}</p>
          <p className="mt-0.5 font-mono text-[10px] text-ink-soft">
            {run.policy_version_id} · {formatTime(run.created_at)}
          </p>
        </div>
        <span
          className={cn(
            "font-mono text-[10px] uppercase tracking-[0.22em]",
            statusColor(run.status),
          )}
        >
          {run.status}
        </span>
        <div>
          <div className="h-1.5 overflow-hidden rounded-full bg-ink/15">
            <div
              className="h-full bg-brass-dark transition-[width]"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-1 font-mono text-[10px] text-ink-soft">
            {run.processed_entries} / {run.total_entries}
          </p>
        </div>
        <div className="text-right">
          <p className="font-heading text-lg text-ink">{agreement}%</p>
          <p className="font-mono text-[10px] text-ink-soft">
            {run.disagreed} disagreements · {run.errored} errors
          </p>
        </div>
      </Link>
    </li>
  );
}

function statusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "running":
    case "queued":
      return "text-approval-amber";
    case "completed":
    case "done":
      return "text-brass-dark";
    case "failed":
    case "errored":
      return "text-wanted-red";
    default:
      return "text-ink-soft";
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toISOString().replace("T", " ").slice(0, 19);
}
