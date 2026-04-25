"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";
import { useAppStore } from "@/lib/store";

type GuardStatus = "checking" | "authed" | "unauthed";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const user = useAppStore((s) => s.user);
  const setUser = useAppStore((s) => s.setUser);
  const setAuthVerified = useAppStore((s) => s.setAuthVerified);

  // If a persisted user is already in the store on mount, show app
  // immediately (no Checking-badge flash). Otherwise wait for getMe.
  const [status, setStatus] = useState<GuardStatus>(
    user ? "authed" : "checking",
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await getMe();
        if (cancelled) return;
        setUser(me);
        setAuthVerified(true);
        setStatus("authed");
      } catch {
        if (cancelled) return;
        // Cookie missing or expired — clear cached user and bounce.
        setAuthVerified(false);
        setUser(null);
        setStatus("unauthed");
        router.replace("/login");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setUser, router]);

  if (status === "checking") {
    return (
      <div className="flex min-h-full flex-1 items-center justify-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
          Checking badge…
        </p>
      </div>
    );
  }

  if (status === "unauthed") return null;

  return <>{children}</>;
}
