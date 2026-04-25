import Link from "next/link";

export default function MarketingLandingPage() {
  return (
    <main className="flex flex-1 items-center justify-center p-16">
      <div className="max-w-xl space-y-6 text-center">
        <div className="flex justify-center text-brass-dark">
          <svg width="72" height="72">
            <use href="#sheriff-star" />
          </svg>
        </div>
        <h1 className="font-heading text-6xl text-wanted-red">AgentSheriff</h1>
        <p className="text-lg text-ink-soft">
          The permission layer for the agentic frontier.
        </p>
        <div>
          <Link
            href="/login"
            className="inline-block border border-ink bg-brass-dark px-5 py-2.5 font-semibold text-parchment transition hover:bg-brass"
          >
            Sign in →
          </Link>
        </div>
        <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
          Marketing landing · full hero + cards coming next commit
        </p>
      </div>
    </main>
  );
}
