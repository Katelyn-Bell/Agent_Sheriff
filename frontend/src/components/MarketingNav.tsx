import Link from "next/link";

export function MarketingNav() {
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
      <Link
        href="/login"
        className="border border-ink bg-parchment px-4 py-2 text-sm font-semibold text-ink transition hover:bg-ink hover:text-parchment"
      >
        Sign in
      </Link>
    </header>
  );
}
