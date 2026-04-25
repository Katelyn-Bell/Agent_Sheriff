export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-16">
      <div className="max-w-xl space-y-6 text-center">
        <h1 className="font-heading text-6xl text-wanted-red">AgentSheriff</h1>
        <p className="text-lg text-ink-soft">
          The permission layer for the agentic frontier.
        </p>
        <div className="flex justify-center gap-2 text-xs uppercase tracking-widest text-brass-dark">
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
