"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "@/lib/store";

const DEBOUNCE_MS = 3000;

export function ReconnectBanner() {
  const connection = useAppStore((s) => s.connection);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (connection !== "disconnected") {
      setVisible(false);
      return;
    }
    const id = setTimeout(() => setVisible(true), DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [connection]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden bg-wanted-red"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center justify-center gap-2 px-4 py-1.5 font-mono text-[11px] uppercase tracking-widest text-parchment">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-parchment" />
            <span>Gateway offline · reconnecting</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
