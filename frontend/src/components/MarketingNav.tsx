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
        // unauthed — leave nav in signed-out state
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
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo-mascot.png"
          alt=""
          aria-hidden
          className="h-8 w-auto"
        />
        <span className="font-heading text-lg leading-none text-ink">
          AgentSheriff
        </span>
      </Link>

      <Link
        href={user ? "/overview" : "/login"}
        className="border border-ink bg-brass-dark px-4 py-2 text-sm font-semibold text-parchment transition hover:bg-brass"
      >
        {user ? "Open dashboard →" : "Sign in →"}
      </Link>
    </header>
  );
}
