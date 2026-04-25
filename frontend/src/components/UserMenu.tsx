"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
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
    <div className="mt-auto flex items-center gap-3 border-t border-brass/40 px-2 pt-4">
      <div className="flex h-8 w-8 items-center justify-center border border-brass-dark bg-parchment-deep font-heading text-sm text-brass-dark">
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
      <button
        type="button"
        onClick={handleSignOut}
        disabled={signingOut}
        title="Sign out"
        className="font-mono text-[10px] uppercase tracking-widest text-ink-soft transition hover:text-wanted-red disabled:opacity-50"
      >
        {signingOut ? "…" : "Out"}
      </button>
    </div>
  );
}
