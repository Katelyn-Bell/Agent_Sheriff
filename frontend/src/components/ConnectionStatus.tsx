"use client";

import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export function ConnectionStatus() {
  const connection = useAppStore((s) => s.connection);
  const label =
    connection === "connected"
      ? "connected"
      : connection === "connecting"
        ? "connecting"
        : "offline";
  const dot =
    connection === "connected"
      ? "bg-brass-dark"
      : connection === "connecting"
        ? "bg-approval-amber animate-pulse"
        : "bg-wanted-red animate-pulse";
  return (
    <div className="mt-auto flex items-center gap-2 border-t border-brass/40 px-3 pt-4 font-mono text-[10px] uppercase tracking-widest text-ink-soft">
      <span className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      <span>{label}</span>
    </div>
  );
}
