"use client";

import Link from "next/link";
import { useState } from "react";

type Step = "welcome" | "tutorial";

export default function OnboardPage() {
  const [step, setStep] = useState<Step>("welcome");

  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <div className="w-full max-w-3xl">
        <StepIndicator step={step} />
        {step === "welcome" ? (
          <Welcome onNext={() => setStep("tutorial")} />
        ) : (
          <Tutorial onBack={() => setStep("welcome")} />
        )}
      </div>
    </main>
  );
}

function StepIndicator({ step }: { step: Step }) {
  const n = step === "welcome" ? 1 : 2;
  return (
    <div className="mb-8 flex items-center justify-center gap-3 font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft">
      <span className={n === 1 ? "text-ink" : undefined}>01 · Welcome</span>
      <span>✦</span>
      <span className={n === 2 ? "text-ink" : undefined}>02 · Tutorial</span>
    </div>
  );
}

function Welcome({ onNext }: { onNext: () => void }) {
  return (
    <section className="border border-brass/40 bg-parchment-deep/40 p-10 text-center shadow-[4px_4px_0_#2b1810]">
      <div className="mb-4 flex justify-center text-brass-dark">
        <svg width="56" height="56" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
      </div>
      <h1 className="font-heading text-4xl text-ink">
        You&apos;re the Sheriff now
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-ink">
        Every AI agent that wants to run a tool — send an email, push code,
        open a browser — now has to come through your office first. You set
        the laws. AgentSheriff enforces them.
      </p>
      <p className="mx-auto mt-3 max-w-xl text-sm text-ink-soft">
        Two quick stops before you ride out: a short tutorial, then you&apos;ll
        describe what your agent does and we&apos;ll draft a starter policy.
      </p>
      <div className="mt-8">
        <button
          type="button"
          onClick={onNext}
          className="border border-ink bg-brass-dark px-5 py-2.5 font-semibold text-parchment transition hover:bg-brass"
        >
          Next →
        </button>
      </div>
    </section>
  );
}

function Tutorial({ onBack }: { onBack: () => void }) {
  const steps = [
    {
      label: "Detect",
      body: "Every tool call is scanned — prompt injections, exfiltration patterns, destructive commands. Nothing runs unexamined.",
    },
    {
      label: "Decide",
      body: "Static rules settle what they can. Borderline calls go to the judge. High-risk calls wait for your badge.",
    },
    {
      label: "Record",
      body: "Every decision, reason, and rationale lands in the Sheriff's Ledger. Replayable. Auditable.",
    },
  ];
  return (
    <section className="border border-brass/40 bg-parchment-deep/40 p-10 shadow-[4px_4px_0_#2b1810]">
      <div className="text-center">
        <h2 className="font-heading text-3xl text-ink">
          How the office works
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-ink-soft">
          Three passes, one decision per tool call. You&apos;ll see all three
          in the Ledger as they happen.
        </p>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {steps.map((step) => (
          <div
            key={step.label}
            className="border border-brass/40 bg-parchment p-5"
          >
            <p className="font-heading text-2xl text-wanted-red">
              {step.label}
            </p>
            <p className="mt-3 text-sm text-ink">{step.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={onBack}
          className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
        >
          ← Back
        </button>
        <Link
          href="/first-ride"
          className="border border-ink bg-brass-dark px-5 py-2.5 font-semibold text-parchment transition hover:bg-brass"
        >
          Let&apos;s ride →
        </Link>
      </div>
    </section>
  );
}
