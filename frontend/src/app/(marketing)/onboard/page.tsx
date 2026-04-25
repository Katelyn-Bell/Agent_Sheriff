"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  BookOpen,
  Compass,
  Gavel,
  Home,
  Scale,
  ShieldCheck,
  Skull,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { generatePolicy } from "@/lib/api";
import { NAV_ROUTES } from "@/lib/nav";
import { useAppStore } from "@/lib/store";

type Step = "welcome" | "tour" | "tailor";

const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  Compass,
  Scale,
  BookOpen,
  ShieldCheck,
  UserRound,
  Skull,
  Gavel,
};

const DEFAULT_TOOL_MANIFEST = [
  "gmail.read_inbox",
  "gmail.send_email",
  "calendar.create_event",
  "calendar.list_events",
  "files.read",
  "files.write",
  "shell.exec",
  "github.push_branch",
  "github.read_repo",
  "browser.open_url",
  "browser.read_page",
];

const DOMAINS = [
  { value: "", label: "No specific domain" },
  { value: "finance", label: "Finance" },
  { value: "support", label: "Customer support" },
  { value: "engineering", label: "Engineering" },
  { value: "research", label: "Research" },
  { value: "other", label: "Other" },
];

const RISK_OPTIONS = [
  {
    value: "strict",
    label: "Strict",
    hint: "Deny by default. Only allow what the rules explicitly permit.",
  },
  {
    value: "balanced",
    label: "Balanced",
    hint: "Allow routine work. Escalate anything sensitive to the Sheriff.",
  },
  {
    value: "loose",
    label: "Loose",
    hint: "Allow most actions. Block only obvious threats.",
  },
];

const TAB_DESCRIPTIONS: Record<string, string> = {
  "/overview":
    "Your main view. Live KPIs, the audit ticker, demo launchers, and the active policy at a glance.",
  "/first-ride":
    "Re-tailor your policy or start a new one from a fresh intent.",
  "/laws":
    "Edit the judge prompt, reorder static rules, and publish new policy versions.",
  "/ledger":
    "Every tool call the gateway has decided on. Filter by decision, agent, or search text.",
  "/approvals":
    "Pending human approvals with live countdowns. Approve, deny, or redact.",
  "/deputies":
    "Your agents. See state, request counts, blocks, and jail or revoke them.",
  "/wanted":
    "Blocked calls pinned as wanted posters. The hall of caught outlaws.",
  "/evals":
    "Replay historical activity against a draft policy before publishing.",
};

const MIN_INTENT_CHARS = 20;

export default function OnboardPage() {
  const [step, setStep] = useState<Step>("welcome");

  return (
    <main className="flex flex-1 items-center justify-center p-10">
      <div className="w-full max-w-5xl">
        <StepIndicator step={step} />
        {step === "welcome" && <Welcome onNext={() => setStep("tour")} />}
        {step === "tour" && (
          <Tour
            onBack={() => setStep("welcome")}
            onNext={() => setStep("tailor")}
          />
        )}
        {step === "tailor" && <Tailor onBack={() => setStep("tour")} />}
      </div>
    </main>
  );
}

function StepIndicator({ step }: { step: Step }) {
  const items: { key: Step; label: string }[] = [
    { key: "welcome", label: "01 Welcome" },
    { key: "tour", label: "02 Tour" },
    { key: "tailor", label: "03 Tailor" },
  ];
  return (
    <div className="mb-12 flex items-center justify-center gap-5 font-mono text-sm uppercase tracking-[0.22em] text-ink-soft">
      {items.map((item, i) => (
        <span key={item.key} className="flex items-center gap-5">
          <span className={item.key === step ? "text-ink" : undefined}>
            {item.label}
          </span>
          {i < items.length - 1 && <span className="text-brass-dark">✦</span>}
        </span>
      ))}
    </div>
  );
}

function Welcome({ onNext }: { onNext: () => void }) {
  return (
    <section className="border border-brass/40 bg-parchment-deep/40 p-16 text-center shadow-[4px_4px_0_#2b1810]">
      <div className="mb-8 flex justify-center text-brass-dark">
        <svg width="96" height="96" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
      </div>
      <h1 className="font-heading text-6xl leading-tight text-ink md:text-7xl">
        You are the Sheriff now
      </h1>
      <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-ink">
        Every AI agent that wants to run a tool (send an email, push code,
        open a browser) now has to come through your office first. You set
        the laws. AgentSheriff enforces them.
      </p>
      <p className="mx-auto mt-5 max-w-xl text-base text-ink-soft">
        Three quick stops: a welcome, a tour of your office, then you
        describe what your agent does and we draft a starter policy.
      </p>
      <div className="mt-10">
        <button
          type="button"
          onClick={onNext}
          className="border border-ink bg-brass-dark px-10 py-4 text-lg font-semibold text-parchment transition hover:bg-brass"
        >
          Next →
        </button>
      </div>
    </section>
  );
}

function Tour({
  onBack,
  onNext,
}: {
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <section className="border border-brass/40 bg-parchment-deep/40 p-12 shadow-[4px_4px_0_#2b1810]">
      <div className="text-center">
        <h2 className="font-heading text-5xl text-ink">Tour the office</h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-ink-soft">
          Every surface you will work with, and what lives there. You can
          leave onboarding at any point to explore.
        </p>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        {NAV_ROUTES.map((route) => {
          const Icon = ICON_MAP[route.icon] ?? Home;
          const desc = TAB_DESCRIPTIONS[route.href] ?? "";
          return (
            <div
              key={route.href}
              className="flex items-start gap-4 border border-brass/40 bg-parchment p-5"
            >
              <div className="mt-1 text-brass-dark">
                <Icon className="h-6 w-6" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-heading text-xl text-ink">{route.label}</p>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">
                  {desc}
                </p>
                <p className="mt-2 font-mono text-[11px] uppercase tracking-widest text-brass-dark">
                  {route.href}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-10 flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="font-mono text-xs uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onNext}
          className="border border-ink bg-brass-dark px-10 py-4 text-lg font-semibold text-parchment transition hover:bg-brass"
        >
          Next: set the laws →
        </button>
      </div>
    </section>
  );
}

function Tailor({ onBack }: { onBack: () => void }) {
  const router = useRouter();
  const setDraftPolicy = useAppStore((s) => s.setDraftPolicy);

  const [name, setName] = useState("");
  const [userIntent, setUserIntent] = useState("");
  const [domain, setDomain] = useState("");
  const [risk, setRisk] = useState("balanced");

  const mutation = useMutation({
    mutationFn: () =>
      generatePolicy({
        name: name.trim(),
        user_intent: `${userIntent.trim()}\n\nRisk posture: ${risk}.`,
        tool_manifest: DEFAULT_TOOL_MANIFEST,
        domain_hint: domain || undefined,
      }),
    onSuccess: (result) => {
      setDraftPolicy({
        name: name.trim(),
        intent_summary: result.intent_summary,
        judge_prompt: result.judge_prompt,
        static_rules: result.static_rules,
        notes: result.notes,
        source: "generated",
      });
      router.push("/laws");
    },
  });

  const createEmptyDraft = () => {
    setDraftPolicy({
      name: name.trim() || "Untitled policy",
      intent_summary: `${userIntent.trim()}\n\nRisk posture: ${risk}.`,
      judge_prompt: "",
      static_rules: [],
      notes: [],
      source: "manual",
    });
    router.push("/laws");
  };

  const canSubmit =
    name.trim().length > 0 && userIntent.trim().length >= MIN_INTENT_CHARS;

  return (
    <section className="border border-brass/40 bg-parchment-deep/40 p-12 shadow-[4px_4px_0_#2b1810]">
      <div className="text-center">
        <h2 className="font-heading text-5xl text-ink">Set the laws</h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-ink-soft">
          Describe what your agent does. We draft a starter policy. You edit
          and publish it from the Laws page.
        </p>
      </div>

      <form
        className="mt-10 space-y-8"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit && !mutation.isPending) mutation.mutate();
        }}
      >
        <Field
          label="Policy name"
          hint="Shows up on every decision and in the Ledger."
        >
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Finance inbox assistant"
            className={inputClass}
            maxLength={80}
            required
          />
        </Field>

        <Field
          label="What does your agent do?"
          hint={`Minimum ${MIN_INTENT_CHARS} characters. More detail gives a better starter policy.`}
        >
          <textarea
            value={userIntent}
            onChange={(e) => setUserIntent(e.target.value)}
            rows={5}
            placeholder="I use this agent to triage my inbox, draft replies to customers, and send invoices to our accountant. It should never email anyone outside the company."
            className={inputClass}
            required
          />
          <div className="mt-1 text-right font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            {userIntent.length} / {MIN_INTENT_CHARS}+ characters
          </div>
        </Field>

        <Field
          label="Domain"
          hint="Optional. Nudges the starter rules toward a vertical."
        >
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className={inputClass}
          >
            {DOMAINS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </Field>

        <Field
          label="Risk posture"
          hint="How aggressive should the Sheriff be by default?"
        >
          <div className="grid gap-3 md:grid-cols-3">
            {RISK_OPTIONS.map((opt) => {
              const selected = risk === opt.value;
              return (
                <label
                  key={opt.value}
                  className={`cursor-pointer border p-4 transition ${
                    selected
                      ? "border-wanted-red bg-parchment"
                      : "border-brass/40 bg-parchment hover:border-brass-dark"
                  }`}
                >
                  <input
                    type="radio"
                    name="risk"
                    value={opt.value}
                    checked={selected}
                    onChange={() => setRisk(opt.value)}
                    className="sr-only"
                  />
                  <p
                    className={`font-heading text-xl ${
                      selected ? "text-wanted-red" : "text-ink"
                    }`}
                  >
                    {opt.label}
                  </p>
                  <p className="mt-2 text-xs text-ink-soft">{opt.hint}</p>
                </label>
              );
            })}
          </div>
        </Field>

        {mutation.isError && (
          <div className="border-l-4 border-wanted-red bg-parchment-deep/60 p-4">
            <p className="font-heading text-base text-wanted-red">
              Could not reach the gateway
            </p>
            <p className="mt-1 text-sm text-ink-soft">
              {mutation.error instanceof Error
                ? mutation.error.message
                : "Unknown error"}
            </p>
            <button
              type="button"
              onClick={createEmptyDraft}
              className="mt-3 text-sm text-wanted-red underline underline-offset-2 hover:opacity-80"
            >
              Start an empty draft instead →
            </button>
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={onBack}
            className="font-mono text-xs uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
          >
            ← Back
          </button>
          <button
            type="submit"
            disabled={!canSubmit || mutation.isPending}
            className="border border-ink bg-brass-dark px-10 py-4 text-lg font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Generating…" : "Draft my policy →"}
          </button>
        </div>
      </form>
    </section>
  );
}

const inputClass =
  "w-full border border-ink/60 bg-parchment px-4 py-3 text-base text-ink transition focus:border-brass focus:outline-none focus:ring-2 focus:ring-brass/30";

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <div className="mb-2 font-heading text-lg text-ink">{label}</div>
      {hint && <div className="mb-3 text-sm text-ink-soft">{hint}</div>}
      {children}
    </label>
  );
}
