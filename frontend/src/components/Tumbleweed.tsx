"use client";

import { motion } from "framer-motion";

interface TumbleweedProps {
  /** Pixel size of the rendered image. Default 120. */
  size?: number;
  /** Direction of travel. Default "right" (left-to-right). */
  direction?: "left" | "right";
  /** Total duration of one trip across, in seconds. Default 12. */
  duration?: number;
  /** Pause between trips, in seconds. Default 5. */
  repeatDelay?: number;
}

export function Tumbleweed({
  size = 120,
  direction = "right",
  duration = 12,
  repeatDelay = 5,
}: TumbleweedProps) {
  const repeat = { repeat: Infinity, repeatDelay } as const;
  const [startX, endX] =
    direction === "right" ? ["-15vw", "115vw"] : ["115vw", "-15vw"];
  const totalRotation = direction === "right" ? 1440 : -1440;

  return (
    // Container straddles the section border so the tumbleweed sits ON
    // the line. overflow-x-clip keeps it offscreen when not in frame;
    // y is visible so the bounces extending up don't get clipped.
    <div
      className="pointer-events-none absolute inset-x-0 z-0 overflow-x-clip"
      style={{ top: -size / 2, height: size }}
    >
      <motion.img
        src="/tumbleweed.png"
        alt=""
        aria-hidden
        className="absolute left-0 top-0 select-none drop-shadow-[0_4px_8px_rgba(43,24,16,0.35)]"
        style={{ height: size, width: "auto" }}
        initial={{ x: startX, y: 0, rotate: 0 }}
        animate={{
          x: endX,
          // 4 decaying bounces with one mid-air gust. easeOut on the way
          // up, easeIn on the way down → real parabolic arcs.
          y: [0, -28, 0, -18, 0, -38, 0, -12, 0, -22, 0],
          rotate: totalRotation,
        }}
        transition={{
          x: { duration, ease: "linear", ...repeat },
          y: {
            duration,
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
            ...repeat,
          },
          rotate: { duration, ease: "linear", ...repeat },
        }}
      />
    </div>
  );
}
