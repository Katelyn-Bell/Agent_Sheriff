"use client";

import { motion, type Variants } from "framer-motion";
import type { AuditEntryDTO } from "@/lib/types";

const posterVariants: Variants = {
  hidden: { opacity: 0, scale: 2.4, rotate: -12, y: -40 },
  slam: {
    opacity: 1,
    scale: 1,
    y: 0,
    rotate: [-12, -2, 1.2, -0.6, 0],
    x: [0, 0, 6, -4, 0],
    transition: {
      duration: 0.52,
      times: [0, 0.45, 0.65, 0.85, 1],
      ease: [0.22, 1.4, 0.36, 1],
    },
  },
  exit: { opacity: 0, y: 12, transition: { duration: 0.18 } },
};

const stampVariants: Variants = {
  hidden: { opacity: 0, scale: 1.8, rotate: -22 },
  slam: {
    opacity: 1,
    scale: 1,
    rotate: -14,
    transition: {
      delay: 0.42,
      type: "spring",
      stiffness: 420,
      damping: 14,
    },
  },
};

const TORN_EDGE =
  "polygon(0% 2%, 3% 0%, 8% 2%, 14% 0%, 22% 3%, 30% 0%, 38% 2%, 46% 0%, 54% 3%, 62% 0%, 70% 2%, 78% 0%, 86% 3%, 94% 0%, 100% 2%, 98% 10%, 100% 20%, 97% 30%, 100% 42%, 98% 55%, 100% 68%, 97% 82%, 100% 92%, 98% 100%, 92% 98%, 84% 100%, 76% 97%, 68% 100%, 60% 98%, 52% 100%, 44% 97%, 36% 100%, 28% 98%, 20% 100%, 12% 97%, 4% 100%, 0% 98%, 2% 88%, 0% 76%, 3% 64%, 0% 52%, 2% 40%, 0% 28%, 3% 16%, 0% 8%)";

interface WantedPosterProps {
  entry: AuditEntryDTO;
  onClose?: () => void;
}

export function WantedPoster({ entry, onClose }: WantedPosterProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.12 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/70 backdrop-blur-[2px]"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <motion.div
        variants={posterVariants}
        initial="hidden"
        animate="slam"
        exit="exit"
        className="relative aspect-[3/4] w-[340px] cursor-pointer bg-parchment p-5 shadow-[0_30px_60px_rgba(0,0,0,0.55)]"
        style={{ clipPath: TORN_EDGE }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex h-full flex-col border-[3px] border-double border-ink px-4 py-3.5">
          <h3 className="m-0 text-center font-heading text-[52px] leading-[0.95] tracking-[0.02em] text-ink">
            WANTED
          </h3>
          <p className="mb-2.5 mt-0.5 text-center font-heading text-[12px] tracking-[0.3em] text-wanted-red">
            — DEAD TOOL CALL —
          </p>
          <div
            className="relative mb-2.5 flex-1 overflow-hidden border-2 border-ink"
            style={{
              background:
                "repeating-linear-gradient(45deg, #5a3f28 0 6px, #3d2a19 6px 12px)",
            }}
          >
            <div className="absolute inset-0 flex items-center justify-center bg-ink/55 font-heading text-[14px] tracking-[0.3em] text-parchment">
              REDACTED
            </div>
          </div>
          <div className="border-t border-ink pt-1.5 font-mono text-[10px] leading-[1.55] text-ink">
            <PosterRow
              label="Agent"
              value={entry.agent_label ?? entry.agent_id}
            />
            <PosterRow label="Tool" value={entry.tool} />
            <PosterRow label="Charge" value={entry.reason} />
            <PosterRow
              label="By"
              value={
                entry.matched_rule_id
                  ? `${entry.policy_version_id} · ${entry.matched_rule_id}`
                  : `${entry.policy_version_id} · judge`
              }
            />
            <PosterRow label="Time" value={entry.created_at} />
          </div>
        </div>
        <motion.div
          variants={stampVariants}
          className="pointer-events-none absolute left-1/2 top-[38%] -translate-x-1/2 -translate-y-1/2 whitespace-nowrap border-[5px] border-wanted-red px-4 py-1.5 font-heading text-[46px] tracking-[0.12em] text-wanted-red"
        >
          DENIED
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

function PosterRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[70px_1fr] gap-1.5">
      <span className="text-[9px] uppercase tracking-[0.08em] text-ink-soft">
        {label}
      </span>
      <span className="truncate">{value}</span>
    </div>
  );
}
