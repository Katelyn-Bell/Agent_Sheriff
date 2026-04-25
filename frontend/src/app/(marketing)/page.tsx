import Link from "next/link";
import { Tumbleweed } from "@/components/Tumbleweed";

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

function Hero() {
  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col items-center gap-6 px-8 py-24 text-center">
      <div className="text-brass-dark">
        <svg width="72" height="72" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
      </div>
      <h1 className="font-heading text-6xl leading-none text-wanted-red md:text-7xl">
        AgentSheriff
      </h1>
      <p className="max-w-xl text-lg text-ink">
        The permission layer for the agentic frontier.
      </p>
      <p className="max-w-2xl text-base text-ink-soft">
        AI agents that can send email, push code, and run commands are
        arriving faster than the safety tools to govern them. AgentSheriff
        sits between every agent and every tool — inspecting, allowing,
        denying, or escalating every action in real time.
      </p>
      <Link
        href="/login"
        className="mt-4 inline-block border border-ink bg-brass-dark px-6 py-3 font-semibold text-parchment transition hover:bg-brass"
      >
        Sign in →
      </Link>
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
      <Tumbleweed />
      <div className="relative z-10 mx-auto w-full max-w-5xl px-8">
        <div className="mb-10 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
            How it works
          </p>
          <h2 className="mt-2 font-heading text-3xl text-ink">
            Three passes, one decision
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.label}
              className="border border-brass/40 bg-parchment p-6"
            >
              <p className="font-heading text-2xl text-wanted-red">
                {step.label}
              </p>
              <p className="mt-3 text-sm text-ink">{step.body}</p>
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
      body: "Deputy Dusty reads an email, creates a calendar event. Two green ledger entries. The gateway stays out of the way.",
    },
    {
      title: "The Outlaw Strikes",
      tag: "deny",
      tagClass: "text-wanted-red",
      body: "A malicious page tells Dusty to exfiltrate contacts. AgentSheriff catches it and a Wanted poster slams the screen.",
    },
    {
      title: "The Sheriff's Call",
      tag: "approval",
      tagClass: "text-approval-amber",
      body: "An invoice with a sensitive attachment pauses for human review. Approve the badge, the mail goes through.",
    },
  ];

  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-5xl px-8">
        <div className="mb-10 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
            The 60-second demo
          </p>
          <h2 className="mt-2 font-heading text-3xl text-ink">
            Three scenes, every time
          </h2>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {scenes.map((scene) => (
            <div
              key={scene.title}
              className="border border-brass/40 bg-parchment-deep/40 p-6"
            >
              <div className="flex items-baseline justify-between">
                <p className="font-heading text-xl text-ink">{scene.title}</p>
                <span
                  className={`font-mono text-[10px] uppercase tracking-[0.22em] ${scene.tagClass}`}
                >
                  {scene.tag}
                </span>
              </div>
              <p className="mt-3 text-sm text-ink-soft">{scene.body}</p>
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
          className="inline-block border border-ink bg-brass-dark px-6 py-3 font-semibold text-parchment transition hover:bg-brass"
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
