"use client";

import { motion } from "framer-motion";

const SHARED_REPEAT = { repeat: Infinity, repeatDelay: 4 } as const;
const SIZE = 80;

export function Tumbleweed() {
  return (
    // Container straddles the section border so the tumbleweed sits ON
    // the line (center of the image aligned with the line, not below it).
    // overflow-x-clip lets it slide off-screen horizontally; vertical is
    // visible so bounces extending up don't get clipped.
    <div
      className="pointer-events-none absolute inset-x-0 z-0 overflow-x-clip"
      style={{ top: -SIZE / 2, height: SIZE }}
    >
      <motion.img
        src="/tumbleweed.png"
        alt=""
        aria-hidden
        className="absolute left-0 top-0 select-none drop-shadow-[0_4px_8px_rgba(43,24,16,0.35)]"
        style={{ height: SIZE, width: "auto" }}
        initial={{ x: "-12vw", y: 0, rotate: 0 }}
        animate={{
          x: "112vw",
          // Decaying-then-rebounding hops, with one big mid-air gust.
          // Negative = up. easeOut on the way up, easeIn on the way down.
          y: [0, -22, 0, -14, 0, -32, 0, -10, 0, -18, 0],
          // Continuous spin tied to forward motion (~4 full rotations).
          rotate: 1440,
        }}
        transition={{
          x: { duration: 11, ease: "linear", ...SHARED_REPEAT },
          y: {
            duration: 11,
            times: [
              0, 0.06, 0.12, 0.2, 0.28, 0.4, 0.52, 0.6, 0.68, 0.78, 0.86,
            ],
            ease: [
              "easeOut",
              "easeIn",
              "easeOut",
              "easeIn",
              "easeOut",
              "easeIn",
              "easeOut",
              "easeIn",
              "easeOut",
              "easeIn",
            ],
            ...SHARED_REPEAT,
          },
          rotate: { duration: 11, ease: "linear", ...SHARED_REPEAT },
        }}
      />
    </div>
  );
}
