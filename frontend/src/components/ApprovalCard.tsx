"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import { resolveApproval } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ApprovalDTO, ApprovalResolution } from "@/lib/types";

const DEFAULT_TOTAL_MS = 120_000;
const URGENT_THRESHOLD_MS = 10_000;

export function ApprovalCard({ approval }: { approval: ApprovalDTO }) {
  const reduceMotion = useReducedMotion();
  const expiresAt = new Date(approval.expires_at).getTime();
  const createdAt = new Date(approval.created_at).getTime();
  const totalMs =
    Number.isFinite(expiresAt) && Number.isFinite(createdAt) && expiresAt > createdAt
      ? expiresAt - createdAt
      : DEFAULT_TOTAL_MS;

  const [msLeft, setMsLeft] = useState(() =>
    Math.max(0, expiresAt - Date.now()),
  );

  useEffect(() => {
    const tick = () => setMsLeft(Math.max(0, expiresAt - Date.now()));
    tick();
    const id = setInterval(tick, 500);
    return () => clearInterval(id);
  }, [expiresAt]);

  const urgent = msLeft > 0 && msLeft <= URGENT_THRESHOLD_MS;
  const pct = Math.max(0, Math.min(100, (msLeft / totalMs) * 100));
  const mm = String(Math.floor(msLeft / 60000)).padStart(2, "0");
  const ss = String(Math.floor((msLeft % 60000) / 1000)).padStart(2, "0");

  const [resolving, setResolving] = useState<ApprovalResolution | null>(null);
  const resolve = async (action: ApprovalResolution) => {
    if (resolving) return;
    setResolving(action);
    try {
      await resolveApproval(approval.id, action);
    } catch (err) {
      console.error("[approval] resolve failed", err);
    } finally {
      setResolving(null);
    }
  };

  return (
    <div className="relative w-full max-w-[420px] rounded-sm border border-ink border-l-[6px] border-l-approval-amber bg-parchment p-5 shadow-[0_12px_28px_rgba(43,24,16,0.18)]">
      <div className="absolute -top-2.5 right-4 rotate-[3deg] border border-ink bg-approval-amber px-2.5 py-1 font-heading text-[11px] uppercase tracking-[0.2em] text-ink">
        Pending
      </div>

      <div className="mb-2 flex items-baseline justify-between gap-3">
        <div className="font-heading text-base text-ink">
          {approval.agent_label ?? approval.agent_id}
        </div>
        <div className="rounded-sm bg-parchment-deep px-2 py-0.5 font-mono text-[11px] text-ink-soft">
          {approval.tool}
        </div>
      </div>

      <p className="mb-2 text-sm leading-relaxed text-ink">
        {approval.user_explanation ?? approval.reason}
      </p>

      <details className="group mb-3.5">
        <summary className="cursor-pointer select-none font-mono text-[11px] uppercase tracking-[0.15em] text-ink-soft hover:text-ink">
          <span className="group-open:hidden">▶ show args</span>
          <span className="hidden group-open:inline">▼ hide args</span>
        </summary>
        <pre className="mt-1.5 max-h-40 overflow-auto rounded-sm bg-parchment-deep p-2 font-mono text-[11px] text-ink leading-relaxed whitespace-pre-wrap break-all">
          {JSON.stringify(approval.args, null, 2)}
        </pre>
      </details>

      <div className="mb-1.5 h-1.5 overflow-hidden rounded-full bg-ink/15">
        <motion.div
          className={cn(
            "h-full",
            urgent ? "bg-wanted-red" : "bg-approval-amber",
          )}
          animate={
            urgent && !reduceMotion
              ? { opacity: [1, 0.55, 1] }
              : { opacity: 1 }
          }
          transition={
            urgent && !reduceMotion
              ? { duration: 1, repeat: Infinity }
              : { duration: 0.2 }
          }
          style={{ width: `${pct}%`, transition: "width 500ms linear" }}
        />
      </div>

      <div className="mb-4 flex items-baseline justify-between font-mono text-[11px] text-ink-soft">
        <span>time to auto-deny</span>
        <motion.span
          className={cn(
            "font-heading text-[15px] tabular-nums",
            urgent ? "text-wanted-red" : "text-ink",
          )}
          animate={
            urgent && !reduceMotion
              ? { opacity: [1, 0.55, 1] }
              : { opacity: 1 }
          }
          transition={
            urgent && !reduceMotion
              ? { duration: 1, repeat: Infinity }
              : { duration: 0.2 }
          }
        >
          {mm}:{ss}
        </motion.span>
      </div>

      <div className="flex gap-2">
        <ActionBtn
          variant="approve"
          disabled={!!resolving}
          onClick={() => resolve("approve")}
        >
          {resolving === "approve" ? "…" : "Approve"}
        </ActionBtn>
        <ActionBtn
          variant="deny"
          disabled={!!resolving}
          onClick={() => resolve("deny")}
        >
          {resolving === "deny" ? "…" : "Deny"}
        </ActionBtn>
        <ActionBtn
          variant="redact"
          disabled={!!resolving}
          onClick={() => resolve("redact")}
        >
          {resolving === "redact" ? "…" : "Redact"}
        </ActionBtn>
      </div>
    </div>
  );
}

function ActionBtn({
  variant,
  ...rest
}: {
  variant: "approve" | "deny" | "redact";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const base =
    "flex-1 border py-2.5 text-[13px] font-semibold transition hover:-translate-y-px disabled:cursor-not-allowed disabled:opacity-50";
  const variantClass =
    variant === "approve"
      ? "border-brass-dark bg-approval-amber text-ink font-bold shadow-[inset_0_-2px_0_#8a5f2d]"
      : variant === "deny"
        ? "border-wanted-red text-wanted-red hover:bg-wanted-red/10"
        : "border-ink-soft text-ink-soft hover:bg-ink-soft/10";
  return (
    <button
      type="button"
      {...rest}
      className={cn(base, variantClass, rest.className)}
    />
  );
}
