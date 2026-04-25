"use client";

import { AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useAppStore } from "@/lib/store";
import type { AuditEntryDTO } from "@/lib/types";
import { WantedPoster } from "./WantedPoster";

const FRESH_MS = 10_000;

export function DenySlamGate() {
  const audit = useAppStore((s) => s.audit);
  const seenIds = useRef<Set<string>>(new Set());
  const [showing, setShowing] = useState<AuditEntryDTO | null>(null);

  useEffect(() => {
    const first = audit[0];
    if (!first) return;
    if (seenIds.current.has(first.id)) return;
    seenIds.current.add(first.id);
    if (first.decision !== "deny") return;
    const age = Date.now() - new Date(first.created_at).getTime();
    if (Number.isNaN(age) || age > FRESH_MS) return;
    setShowing(first);
  }, [audit]);

  return (
    <AnimatePresence>
      {showing && (
        <WantedPoster entry={showing} onClose={() => setShowing(null)} />
      )}
    </AnimatePresence>
  );
}
