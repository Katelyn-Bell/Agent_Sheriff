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
  const [status, setStatus] = useState<GuardStatus>(
    user ? "authed" : "checking",
  );

  useEffect(() => {
    if (user) {
      setStatus("authed");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const me = await getMe();
        if (cancelled) return;
        setUser(me);
        setStatus("authed");
      } catch {
        if (cancelled) return;
        setStatus("unauthed");
        router.replace("/login");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, setUser, router]);

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
