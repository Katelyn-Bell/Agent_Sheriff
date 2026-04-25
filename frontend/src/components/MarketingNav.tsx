import Link from "next/link";

export function MarketingNav() {
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
        href="/login"
        className="border border-ink bg-brass-dark px-4 py-2 text-sm font-semibold text-parchment transition hover:bg-brass"
      >
        Sign in →
      </Link>
    </header>
  );
}
