"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Compass,
  Gavel,
  Home,
  Scale,
  ShieldCheck,
  Skull,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { NAV_ROUTES } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { UserMenu } from "./UserMenu";

const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  Compass,
  Scale,
  BookOpen,
  ShieldCheck,
  UserRound,
  Skull,
  Gavel,
};

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col gap-6 border-r border-brass/40 bg-parchment-deep/60 px-4 py-6">
      <Link
        href="/overview"
        className="flex items-center gap-3 px-2 text-brass-dark transition hover:text-wanted-red"
      >
        <svg width="32" height="32" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
        <span className="font-heading text-xl leading-none text-ink">
          AgentSheriff
        </span>
      </Link>

      <nav className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
        <div className="mb-2 px-3 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
          Operations
        </div>
        {NAV_ROUTES.map((route) => {
          const Icon = ICON_MAP[route.icon] ?? Home;
          const active = isActive(pathname, route.href);
          return (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "flex items-center gap-3 border-l-2 py-2 pr-3 pl-[10px] text-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brass",
                active
                  ? "border-wanted-red bg-parchment/60 text-wanted-red"
                  : "border-transparent text-ink-soft hover:border-brass/60 hover:text-ink",
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{route.label}</span>
            </Link>
          );
        })}
      </nav>

      <UserMenu />
    </aside>
  );
}
