"use client";

import { useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { PageHeader } from "@/components/PageHeader";
import { WantedPoster } from "@/components/WantedPoster";
import { useAppStore } from "@/lib/store";
import type { AuditEntryDTO } from "@/lib/types";

export default function WantedBoardPage() {
  const audit = useAppStore((s) => s.audit);
  const denies = useMemo(
    () => audit.filter((e) => e.decision === "deny").slice(0, 12),
    [audit],
  );
  const [showing, setShowing] = useState<AuditEntryDTO | null>(null);

  return (
    <section>
      <PageHeader
        title="Wanted"
        subtitle={
          denies.length === 0
            ? "No outlaws on file"
            : `${denies.length} outstanding · click a poster to open`
        }
      />

      {denies.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
          <p className="font-heading text-xl text-ink">No outlaws on file</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
            Denied tool calls with high risk show up here. Run the injection
            scenario from the Town Overview to summon one.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {denies.map((e) => (
            <MiniPoster
              key={e.id}
              entry={e}
              onClick={() => setShowing(e)}
            />
          ))}
        </div>
      )}

      <AnimatePresence>
        {showing && (
          <WantedPoster entry={showing} onClose={() => setShowing(null)} />
        )}
      </AnimatePresence>
    </section>
  );
}

function MiniPoster({
  entry,
  onClick,
}: {
  entry: AuditEntryDTO;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative block w-full cursor-pointer overflow-hidden border-2 border-ink bg-parchment p-3 text-left transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(43,24,16,0.25)]"
    >
      <div className="flex flex-col border-[2px] border-double border-ink px-3 py-3">
        <h3 className="text-center font-heading text-3xl leading-none text-ink">
          WANTED
        </h3>
        <p className="mt-1 text-center font-heading text-[9px] tracking-[0.3em] text-wanted-red">
          — DEAD TOOL CALL —
        </p>

        <div className="my-3 flex items-center justify-center">
          <span className="rotate-[-6deg] border-[3px] border-wanted-red px-3 py-1 font-heading text-2xl tracking-[0.12em] text-wanted-red">
            DENIED
          </span>
        </div>

        <div className="space-y-1.5 border-t border-ink pt-2 font-mono text-[10px] leading-tight text-ink">
          <PosterField label="Agent" value={entry.agent_label ?? entry.agent_id} />
          <PosterField label="Tool" value={entry.tool} mono />
          <PosterField label="Charge" value={entry.reason} multiline />
          <PosterField label="Time" value={formatTime(entry.ts)} />
        </div>
      </div>
    </button>
  );
}

function PosterField({
  label,
  value,
  mono = false,
  multiline = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  multiline?: boolean;
}) {
  return (
    <div>
      <div className="text-[8px] uppercase tracking-[0.22em] text-ink-soft">
        {label}
      </div>
      <div
        className={`text-[11px] leading-snug text-ink ${mono ? "font-mono" : ""} ${multiline ? "line-clamp-2" : "truncate"}`}
      >
        {value}
      </div>
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
