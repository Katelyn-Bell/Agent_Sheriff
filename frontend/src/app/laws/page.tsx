"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createPolicy, publishPolicy } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore, type DraftPolicy } from "@/lib/store";
import type { StaticRuleDTO } from "@/lib/types";

export default function TownLawsPage() {
  const draft = useAppStore((s) => s.draftPolicy);

  return (
    <section>
      <PageHeader
        title="Town Laws"
        subtitle="Policy workbench · draft · publish"
        actions={
          draft && (
            <Link
              href="/first-ride"
              className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
            >
              Start over →
            </Link>
          )
        }
      />

      <div className="grid gap-8 lg:grid-cols-[1fr_300px]">
        <div>{draft ? <DraftEditor /> : <EmptyState />}</div>
        <aside className="space-y-4">
          <PublishedPanel />
        </aside>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-8 text-center">
      <p className="font-heading text-lg text-ink">No draft loaded</p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
        Policies are drafted, edited, and published from here. Start a new draft
        by generating one from intent.
      </p>
      <Link
        href="/first-ride"
        className="mt-4 inline-block border border-ink bg-brass-dark px-4 py-2 text-sm font-semibold text-parchment transition hover:bg-brass"
      >
        Go to First Ride
      </Link>
    </div>
  );
}

function DraftEditor() {
  const router = useRouter();
  const draft = useAppStore((s) => s.draftPolicy);
  const updateDraftPolicy = useAppStore((s) => s.updateDraftPolicy);
  const setDraftPolicy = useAppStore((s) => s.setDraftPolicy);

  const publishMutation = useMutation({
    mutationFn: async (d: DraftPolicy) => {
      const created = await createPolicy({
        name: d.name,
        intent_summary: d.intent_summary,
        judge_prompt: d.judge_prompt,
        static_rules: d.static_rules,
      });
      return publishPolicy(created.id);
    },
    onSuccess: () => {
      setDraftPolicy(null);
      router.push("/");
    },
  });

  if (!draft) return null;

  const canPublish =
    draft.name.trim().length > 0 &&
    draft.intent_summary.trim().length > 0 &&
    !publishMutation.isPending;

  const handlePublish = () => {
    if (!canPublish) return;
    const ok = window.confirm(
      "Publishing makes this the active policy. Old versions stay in history. Continue?",
    );
    if (ok) publishMutation.mutate(draft);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <span className="border border-brass-dark bg-approval-amber px-2 py-0.5 font-heading text-xs uppercase tracking-[0.22em] text-ink">
          Draft · {draft.source}
        </span>
        <input
          type="text"
          value={draft.name}
          onChange={(e) => updateDraftPolicy({ name: e.target.value })}
          placeholder="Policy name"
          className="flex-1 border-b border-ink/40 bg-transparent py-1 font-heading text-2xl text-ink focus:border-brass focus:outline-none"
        />
      </div>

      <Panel title="Intent summary">
        <textarea
          value={draft.intent_summary}
          onChange={(e) =>
            updateDraftPolicy({ intent_summary: e.target.value })
          }
          rows={3}
          className={editorTextareaClass}
          placeholder="One-paragraph description of what this agent is for."
        />
      </Panel>

      <Panel title="Judge prompt">
        <textarea
          value={draft.judge_prompt}
          onChange={(e) => updateDraftPolicy({ judge_prompt: e.target.value })}
          rows={10}
          className={`${editorTextareaClass} font-mono text-xs leading-relaxed`}
          placeholder="Natural-language instructions for the LLM judge when rules don't settle a call."
        />
      </Panel>

      <Panel
        title={`Static rules (${draft.static_rules.length})`}
        action={
          <button
            type="button"
            onClick={() =>
              updateDraftPolicy({
                static_rules: [...draft.static_rules, makeBlankRule()],
              })
            }
            className="font-mono text-[11px] uppercase tracking-widest text-brass-dark underline-offset-4 hover:text-ink hover:underline"
          >
            + Add rule
          </button>
        }
      >
        {draft.static_rules.length === 0 ? (
          <p className="text-sm text-ink-soft">
            No static rules. Add some above, or let the judge decide everything.
          </p>
        ) : (
          <ol className="space-y-2">
            {draft.static_rules.map((rule, idx) => (
              <RuleRow
                key={rule.id}
                rule={rule}
                index={idx}
                total={draft.static_rules.length}
                onMove={(dir) =>
                  updateDraftPolicy({
                    static_rules: moveRule(draft.static_rules, idx, dir),
                  })
                }
                onDelete={() =>
                  updateDraftPolicy({
                    static_rules: draft.static_rules.filter(
                      (_, i) => i !== idx,
                    ),
                  })
                }
              />
            ))}
          </ol>
        )}
      </Panel>

      {draft.notes.length > 0 && (
        <Panel title="Generation notes">
          <ul className="list-disc space-y-1 pl-5 text-sm text-ink-soft">
            {draft.notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </Panel>
      )}

      {publishMutation.isError && (
        <div className="border-l-4 border-wanted-red bg-parchment-deep/60 p-4">
          <p className="font-heading text-base text-wanted-red">
            Couldn&apos;t publish
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            {publishMutation.error instanceof Error
              ? publishMutation.error.message
              : "Unknown error"}
          </p>
        </div>
      )}

      <div className="flex items-center gap-4 border-t border-brass/40 pt-6">
        <button
          type="button"
          onClick={handlePublish}
          disabled={!canPublish}
          className="border border-ink bg-brass-dark px-5 py-2.5 font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
        >
          {publishMutation.isPending ? "Publishing…" : "Publish draft"}
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Discard this draft?")) setDraftPolicy(null);
          }}
          className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-wanted-red hover:underline"
        >
          Discard draft
        </button>
      </div>
    </div>
  );
}

function PublishedPanel() {
  const latestPolicy = useAppStore((s) => s.latestPolicy);
  return (
    <div className="border border-brass/40 bg-parchment-deep/40 p-4">
      <div className="mb-3 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
        Currently published
      </div>
      {latestPolicy ? (
        <>
          <p className="font-heading text-base text-ink">{latestPolicy.name}</p>
          <p className="mt-1 font-mono text-xs text-ink-soft">
            v{latestPolicy.version} · {latestPolicy.static_rules.length} rules
          </p>
          <p className="mt-3 text-xs text-ink-soft">
            {latestPolicy.intent_summary}
          </p>
        </>
      ) : (
        <p className="text-sm text-ink-soft">
          No published version yet. Your first publish becomes v1.
        </p>
      )}
    </div>
  );
}

function RuleRow({
  rule,
  index,
  total,
  onMove,
  onDelete,
}: {
  rule: StaticRuleDTO;
  index: number;
  total: number;
  onMove: (dir: -1 | 1) => void;
  onDelete: () => void;
}) {
  return (
    <li className="border border-ink/20 bg-parchment px-3 py-2">
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-ink-soft">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="font-heading text-sm text-ink">{rule.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`font-mono text-[10px] uppercase tracking-widest ${actionColor(rule.action)}`}>
            {rule.action}
          </span>
          <button
            type="button"
            onClick={() => onMove(-1)}
            disabled={index === 0}
            className="px-1 text-ink-soft transition hover:text-ink disabled:cursor-not-allowed disabled:opacity-30"
            aria-label="Move up"
          >
            ↑
          </button>
          <button
            type="button"
            onClick={() => onMove(1)}
            disabled={index === total - 1}
            className="px-1 text-ink-soft transition hover:text-ink disabled:cursor-not-allowed disabled:opacity-30"
            aria-label="Move down"
          >
            ↓
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="px-1 text-ink-soft transition hover:text-wanted-red"
            aria-label="Delete rule"
          >
            ✕
          </button>
        </div>
      </div>
      <p className="mt-1 font-mono text-[10px] text-ink-soft">
        {rule.tool_match.kind}: <strong className="text-ink">{rule.tool_match.value}</strong>
      </p>
      {rule.reason && (
        <p className="mt-1 text-xs text-ink-soft">{rule.reason}</p>
      )}
    </li>
  );
}

function Panel({
  title,
  action,
  children,
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-brass/40 bg-parchment-deep/40 p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
          {title}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

const editorTextareaClass =
  "w-full border border-ink/30 bg-parchment px-3 py-2 text-ink transition focus:border-brass focus:outline-none focus:ring-2 focus:ring-brass/30";

function moveRule(
  rules: StaticRuleDTO[],
  from: number,
  direction: -1 | 1,
): StaticRuleDTO[] {
  const to = from + direction;
  if (to < 0 || to >= rules.length) return rules;
  const next = [...rules];
  [next[from], next[to]] = [next[to], next[from]];
  return next;
}

function makeBlankRule(): StaticRuleDTO {
  return {
    id: `rule_${Math.random().toString(36).slice(2, 10)}`,
    name: "New rule",
    tool_match: { kind: "namespace", value: "example.*" },
    arg_predicates: [],
    action: "delegate_to_judge",
    stop_on_match: true,
  };
}

function actionColor(action: StaticRuleDTO["action"]): string {
  switch (action) {
    case "allow":
      return "text-brass-dark";
    case "deny":
      return "text-wanted-red";
    case "require_approval":
      return "text-approval-amber";
    case "delegate_to_judge":
      return "text-ink-soft";
  }
}
