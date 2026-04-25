"use client";

import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store";

export default function TownLawsPage() {
  const draft = useAppStore((s) => s.draftPolicy);

  return (
    <section>
      <PageHeader
        title="Town Laws"
        subtitle="Policy workbench · draft · publish"
      />

      {draft ? <DraftPreview /> : <EmptyState />}
    </section>
  );
}

function DraftPreview() {
  const draft = useAppStore((s) => s.draftPolicy);
  if (!draft) return null;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <span className="border border-brass-dark bg-approval-amber px-2 py-0.5 font-heading text-xs uppercase tracking-[0.22em] text-ink">
          Draft · {draft.source}
        </span>
        <span className="font-heading text-2xl text-ink">{draft.name}</span>
      </div>

      <Panel title="Intent summary">
        <p className="whitespace-pre-wrap text-ink">
          {draft.intent_summary || (
            <span className="text-ink-soft">No intent summary yet.</span>
          )}
        </p>
      </Panel>

      <Panel title="Judge prompt">
        {draft.judge_prompt ? (
          <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ink">
            {draft.judge_prompt}
          </pre>
        ) : (
          <p className="text-ink-soft">Not generated yet.</p>
        )}
      </Panel>

      <Panel title={`Static rules (${draft.static_rules.length})`}>
        {draft.static_rules.length === 0 ? (
          <p className="text-ink-soft">No static rules drafted.</p>
        ) : (
          <ol className="space-y-2">
            {draft.static_rules.map((rule) => (
              <li
                key={rule.id}
                className="border border-ink/20 bg-parchment px-3 py-2"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <span className="font-heading text-sm text-ink">
                    {rule.name}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-ink-soft">
                    {rule.action}
                  </span>
                </div>
                {rule.reason && (
                  <p className="mt-1 text-xs text-ink-soft">{rule.reason}</p>
                )}
              </li>
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

      <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
        Full workbench (edit · reorder · publish) lands in Run 2B.
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-8 text-center">
      <p className="font-heading text-lg text-ink">No draft loaded</p>
      <p className="mt-2 text-sm text-ink-soft">
        Head to First Ride to generate one, or the full workbench will let you
        start empty once it lands in Run 2B.
      </p>
    </div>
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
