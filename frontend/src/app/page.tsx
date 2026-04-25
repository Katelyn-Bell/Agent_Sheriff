export default function Home() {
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
        <div className="flex justify-center gap-2 font-mono text-xs uppercase tracking-widest text-brass-dark">
          <span>Parchment</span>
          <span>·</span>
          <span>Brass</span>
          <span>·</span>
          <span>Wanted Red</span>
          <span>·</span>
          <span>Approval Amber</span>
        </div>
      </div>
    </main>
  );
}
