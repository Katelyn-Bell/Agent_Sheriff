"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { LogOut } from "lucide-react";
import { logout } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export function UserMenu() {
  const router = useRouter();
  const user = useAppStore((s) => s.user);
  const setUser = useAppStore((s) => s.setUser);
  const [signingOut, setSigningOut] = useState(false);

  if (!user) return null;

  const handleSignOut = async () => {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await logout();
    } catch {
      // offline or session already gone — clear local state anyway
    } finally {
      setUser(null);
      router.push("/");
    }
  };

  const initial =
    user.name?.trim().charAt(0).toUpperCase() ||
    user.email?.trim().charAt(0).toUpperCase() ||
    "?";

  return (
    <div className="mt-auto space-y-3 border-t border-brass/40 px-2 pt-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center border border-brass-dark bg-parchment-deep font-heading text-base text-brass-dark">
          {user.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={user.avatar_url}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            <span>{initial}</span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-heading text-sm leading-tight text-ink">
            {user.name}
          </p>
          <p className="truncate font-mono text-[10px] leading-tight text-ink-soft">
            {user.email}
          </p>
        </div>
      </div>
      <button
        type="button"
        onClick={handleSignOut}
        disabled={signingOut}
        className="flex w-full items-center justify-center gap-2 border border-ink/40 bg-parchment px-3 py-2 font-mono text-[11px] uppercase tracking-[0.2em] text-ink transition hover:border-wanted-red hover:bg-wanted-red/5 hover:text-wanted-red disabled:opacity-50"
      >
        <LogOut className="h-3.5 w-3.5" />
        {signingOut ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}
