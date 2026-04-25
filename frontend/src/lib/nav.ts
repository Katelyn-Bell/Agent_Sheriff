export interface NavRoute {
  href: string;
  label: string;
  icon: string;
}

export const NAV_ROUTES: readonly NavRoute[] = [
  { href: "/", label: "Town Overview", icon: "Home" },
  { href: "/first-ride", label: "First Ride", icon: "Compass" },
  { href: "/laws", label: "Town Laws", icon: "Scale" },
  { href: "/ledger", label: "Sheriff's Ledger", icon: "BookOpen" },
  { href: "/approvals", label: "Badge Approval", icon: "ShieldCheck" },
  { href: "/deputies", label: "Deputies", icon: "UserRound" },
  { href: "/wanted", label: "Wanted Board", icon: "Skull" },
  { href: "/evals", label: "Trial Records", icon: "Gavel" },
] as const;
