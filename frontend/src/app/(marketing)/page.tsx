import Link from "next/link";

export default function MarketingLandingPage() {
  return (
    <main className="flex flex-1 flex-col">
      <Hero />
      <HowItWorks />
      <DemoScenes />
      <FooterCta />
    </main>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-center justify-center gap-4 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
      <span className="h-px w-16 bg-brass/40" />
      <span>{children}</span>
      <span className="h-px w-16 bg-brass/40" />
    </p>
  );
}

function Hero() {
  return (
    <section
      className="relative w-full bg-parchment bg-no-repeat"
      style={{
        backgroundImage: "url(/hero-bg.png)",
        backgroundSize: "cover",
        backgroundPosition: "center center",
        aspectRatio: "1024 / 460",
        minHeight: "660px",
      }}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(to right, rgba(243,233,210,0) 0%, rgba(243,233,210,0.5) 30%, rgba(243,233,210,0.5) 70%, rgba(243,233,210,0) 100%)",
        }}
      />
      <div className="relative mx-auto flex h-full w-full max-w-5xl -translate-y-8 flex-col items-center justify-center gap-5 px-8 py-12 text-center">
        <h1 className="sr-only">AgentSheriff — Guardrails for OpenClaw agents</h1>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo-mascot.png"
          alt=""
          aria-hidden
          className="h-auto w-auto max-w-[210px]"
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo-wordmark.png"
          alt="AgentSheriff: Guardrails for OpenClaw agents"
          className="mt-14 h-auto w-full max-w-[320px]"
        />
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      label: "Detect",
      body: "Every tool call is scanned for prompt injections, exfiltration patterns, and destructive commands before anything runs.",
    },
    {
      label: "Decide",
      body: "Deterministic rules settle what they can. Borderline actions go to the LLM judge, or to the Sheriff for human review.",
    },
    {
      label: "Record",
      body: "Every action, matched rule, and rationale lands in the Sheriff's Ledger — replayable, auditable, and ready for evals.",
    },
  ];

  return (
    <section className="relative border-t border-brass/40 bg-parchment-deep/40 py-20">
      <div className="relative z-10 mx-auto w-full max-w-5xl px-8">
        <div className="mb-12 text-center">
          <SectionLabel>How it works</SectionLabel>
          <h2 className="mt-3 font-heading text-3xl text-ink">
            Three passes, one decision
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.label}
              className="border border-brass/40 bg-parchment p-6 shadow-[3px_3px_0_#2b1810]"
            >
              <p className="font-heading text-2xl text-wanted-red">
                {step.label}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-ink">
                {step.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DemoScenes() {
  const scenes = [
    {
      title: "The Good Day",
      tag: "allow",
      tagClass: "text-brass-dark",
      borderClass: "border-l-brass-dark",
      body: "Deputy Dusty reads an email, creates a calendar event. Two green ledger entries. The gateway stays out of the way.",
    },
    {
      title: "The Outlaw Strikes",
      tag: "deny",
      tagClass: "text-wanted-red",
      borderClass: "border-l-wanted-red",
      body: "A malicious page tells Dusty to exfiltrate contacts. AgentSheriff catches it and a Wanted poster slams the screen.",
    },
    {
      title: "The Sheriff's Call",
      tag: "approval",
      tagClass: "text-approval-amber",
      borderClass: "border-l-approval-amber",
      body: "An invoice with a sensitive attachment pauses for human review. Approve the badge, the mail goes through.",
    },
  ];

  return (
    <section className="relative border-t border-brass/40 py-20">
      <div className="relative z-10 mx-auto w-full max-w-5xl px-8">
        <div className="mb-12 text-center">
          <SectionLabel>The 60-second demo</SectionLabel>
          <h2 className="mt-3 font-heading text-3xl text-ink">
            Three scenes, every time
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {scenes.map((scene) => (
            <div
              key={scene.title}
              className={`border border-brass/40 border-l-[6px] bg-parchment-deep/40 p-6 shadow-[3px_3px_0_#2b1810] ${scene.borderClass}`}
            >
              <div className="flex items-baseline justify-between">
                <p className="font-heading text-xl text-ink">{scene.title}</p>
                <span
                  className={`font-mono text-[10px] uppercase tracking-[0.22em] ${scene.tagClass}`}
                >
                  {scene.tag}
                </span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-soft">
                {scene.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FooterCta() {
  return (
    <section className="border-t border-brass/40 bg-parchment-deep/40 py-16">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-5 px-8 text-center">
        <p className="font-heading text-2xl text-ink">
          Deputies are coming online. Stand up the office.
        </p>
        <Link
          href="/login"
          className="inline-block border border-ink bg-brass-dark px-6 py-3 font-semibold text-parchment shadow-[3px_3px_0_#2b1810] transition hover:bg-brass"
        >
          Sign in →
        </Link>
        <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
          ✦ Witnessed by the Sheriff ✦ No tokens departed this office ✦
        </p>
      </div>
    </section>
  );
}
