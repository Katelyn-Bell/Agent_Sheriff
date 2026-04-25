export interface NavRoute {
  href: string;
  label: string;
  icon: string;
}

export const NAV_ROUTES: readonly NavRoute[] = [
  { href: "/overview", label: "Overview", icon: "Home" },
  { href: "/new-policy", label: "New Policy", icon: "Compass" },
  { href: "/laws", label: "Laws", icon: "Scale" },
  { href: "/ledger", label: "Ledger", icon: "BookOpen" },
  { href: "/approvals", label: "Approvals", icon: "ShieldCheck" },
  { href: "/deputies", label: "Deputies", icon: "UserRound" },
  { href: "/wanted", label: "Wanted", icon: "Skull" },
  { href: "/evals", label: "Evals", icon: "Gavel" },
] as const;
