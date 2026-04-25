"use client";

import Link from "next/link";
import { useEffect } from "react";
import { getMe } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export function MarketingNav() {
  const user = useAppStore((s) => s.user);
  const setUser = useAppStore((s) => s.setUser);

  useEffect(() => {
    if (user) return;
    let cancelled = false;
    (async () => {
      try {
        const me = await getMe();
        if (!cancelled) setUser(me);
      } catch {
        // unauthed; leave nav in signed-out state
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, setUser]);

  return (
    <header className="flex items-center justify-between border-b border-brass/40 bg-parchment-deep/40 px-8 py-4">
      <Link
        href="/"
        className="flex items-center gap-3 text-brass-dark transition hover:text-wanted-red"
      >
        <svg width="28" height="28" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
        <span className="font-heading text-lg leading-none text-ink">
          AgentSheriff
        </span>
      </Link>

      {user ? (
        <Link
          href="/overview"
          className="border border-ink bg-brass-dark px-4 py-2 text-sm font-semibold text-parchment transition hover:bg-brass"
        >
          Open dashboard →
        </Link>
      ) : (
        <Link
          href="/login"
          className="border border-ink bg-parchment px-4 py-2 text-sm font-semibold text-ink transition hover:bg-ink hover:text-parchment"
        >
          Sign in
        </Link>
      )}
    </header>
  );
}
