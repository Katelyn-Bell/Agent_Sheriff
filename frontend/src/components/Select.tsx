"use client";

import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: readonly SelectOption[];
  placeholder?: string;
  className?: string;
  size?: "sm" | "md";
  id?: string;
}

export function Select({
  value,
  onChange,
  options,
  placeholder = "Choose…",
  className,
  size = "md",
  id,
}: SelectProps) {
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState<number>(-1);
  const [maxHeight, setMaxHeight] = useState<number>(256);
  const ref = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const current = options.find((o) => o.value === value);

  // Always open downward. Cap the panel at 240px (about 6 rows) so any
  // longer list always has a visible scrollbar, and shrink further if the
  // viewport below is smaller than that.
  useEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const margin = 12;
    const below = window.innerHeight - rect.bottom - margin;
    setMaxHeight(Math.max(96, Math.min(240, below)));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setHighlighted(options.findIndex((o) => o.value === value));
  }, [open, options, value]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onResize = () => setOpen(false);
    window.addEventListener("mousedown", onClick);
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onResize, true);
    return () => {
      window.removeEventListener("mousedown", onClick);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onResize, true);
    };
  }, [open]);

  const handleKey = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(true);
      }
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, options.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const opt = options[highlighted];
      if (opt) {
        onChange(opt.value);
        setOpen(false);
      }
    }
  };

  const triggerSize =
    size === "sm" ? "px-3 py-1.5 text-sm" : "px-4 py-3 text-base";
  const optionSize =
    size === "sm" ? "px-3 py-1.5 text-sm" : "px-4 py-2.5 text-sm";

  return (
    <div
      ref={ref}
      onKeyDown={handleKey}
      className={cn("relative", className)}
    >
      <button
        type="button"
        ref={triggerRef}
        id={id}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          "flex w-full items-center justify-between border border-ink/60 bg-parchment text-ink transition focus:border-brass focus:outline-none focus:ring-2 focus:ring-brass/30",
          triggerSize,
          open && "border-brass ring-2 ring-brass/30",
        )}
      >
        <span className={cn(!current && "text-ink-soft")}>
          {current?.label ?? placeholder}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-brass-dark transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <ul
          role="listbox"
          style={{ maxHeight }}
          className="absolute left-0 right-0 top-full z-20 mt-1 overflow-y-auto overflow-x-hidden border border-ink bg-parchment shadow-[4px_4px_0_#2b1810]"
        >
          {options.map((opt, i) => {
            const selected = opt.value === value;
            const highlight = i === highlighted;
            return (
              <li key={opt.value} role="option" aria-selected={selected}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  onMouseEnter={() => setHighlighted(i)}
                  className={cn(
                    "flex w-full items-center justify-between text-left transition",
                    optionSize,
                    selected
                      ? "bg-brass-dark text-parchment"
                      : highlight
                        ? "bg-parchment-deep text-ink"
                        : "text-ink",
                  )}
                >
                  <span>{opt.label}</span>
                  {selected && (
                    <span className="font-mono text-[10px] uppercase tracking-widest opacity-80">
                      ✓
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
