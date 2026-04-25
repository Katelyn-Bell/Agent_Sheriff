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
        title="Wanted Board"
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
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
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
      className="group block aspect-[3/4] w-full cursor-pointer border border-ink bg-parchment p-3 text-left transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(43,24,16,0.25)]"
    >
      <div className="flex h-full flex-col border-[2px] border-double border-ink px-3 py-2.5">
        <h3 className="text-center font-heading text-2xl leading-none text-ink">
          WANTED
        </h3>
        <p className="mb-2 mt-0.5 text-center font-heading text-[9px] tracking-[0.3em] text-wanted-red">
          — DEAD TOOL CALL —
        </p>
        <div
          className="relative mb-2 flex flex-1 items-center justify-center overflow-hidden border border-ink"
          style={{
            background:
              "repeating-linear-gradient(45deg, #5a3f28 0 6px, #3d2a19 6px 12px)",
          }}
        >
          <span className="bg-ink/60 px-2 py-0.5 font-heading text-[10px] tracking-[0.3em] text-parchment">
            REDACTED
          </span>
        </div>
        <div className="border-t border-ink pt-1 font-mono text-[9px] leading-[1.4] text-ink">
          <p className="truncate">
            <span className="text-ink-soft">Agent: </span>
            {entry.agent_label ?? entry.agent_id}
          </p>
          <p className="truncate">
            <span className="text-ink-soft">Tool: </span>
            {entry.tool}
          </p>
          <p className="line-clamp-2">
            <span className="text-ink-soft">Charge: </span>
            {entry.reason}
          </p>
        </div>
      </div>
    </button>
  );
}
