"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  BookOpen,
  Calendar,
  Code,
  Compass,
  FolderOpen,
  Gavel,
  GitBranch,
  Globe,
  HelpCircle,
  Home,
  Mail,
  MessageSquare,
  Scale,
  Search,
  ShieldCheck,
  Skull,
  Sparkles,
  Terminal,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { generatePolicy } from "@/lib/api";
import { NAV_ROUTES } from "@/lib/nav";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface StepDef {
  key: string;
  label: string;
}

const STEPS: StepDef[] = [
  { key: "welcome", label: "Welcome" },
  { key: "tour", label: "Tour" },
  { key: "use-case", label: "Use case" },
  { key: "tools", label: "Tools" },
  { key: "concerns", label: "Concerns" },
  { key: "risk", label: "Risk posture" },
  { key: "notes", label: "Notes" },
  { key: "name", label: "Save as" },
];

const NAV_ICON_MAP: Record<string, LucideIcon> = {
  Home,
  Compass,
  Scale,
  BookOpen,
  ShieldCheck,
  UserRound,
  Skull,
  Gavel,
};

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

interface UseCaseOption {
  value: string;
  label: string;
  icon: LucideIcon;
  summary: string;
}

const USE_CASES: UseCaseOption[] = [
  {
    value: "email",
    label: "Email assistant",
    icon: Mail,
    summary: "Triages inbox, drafts replies, sends messages.",
  },
  {
    value: "coding",
    label: "Coding agent",
    icon: Code,
    summary: "Reads, writes, and pushes code.",
  },
  {
    value: "research",
    label: "Research",
    icon: Search,
    summary: "Browses, reads pages, summarizes findings.",
  },
  {
    value: "support",
    label: "Customer support",
    icon: MessageSquare,
    summary: "Replies to tickets, looks up records.",
  },
  {
    value: "personal",
    label: "Personal automation",
    icon: Sparkles,
    summary: "Calendar, notes, household chores.",
  },
  {
    value: "other",
    label: "Other",
    icon: HelpCircle,
    summary: "Tell us in the notes step.",
  },
];

interface ToolOption {
  value: string;
  label: string;
  icon: LucideIcon;
  manifest: string[];
}

const TOOLS: ToolOption[] = [
  {
    value: "gmail",
    label: "Gmail",
    icon: Mail,
    manifest: ["gmail.read_inbox", "gmail.send_email"],
  },
  {
    value: "calendar",
    label: "Calendar",
    icon: Calendar,
    manifest: ["calendar.create_event", "calendar.list_events"],
  },
  {
    value: "files",
    label: "Files",
    icon: FolderOpen,
    manifest: ["files.read", "files.write"],
  },
  {
    value: "shell",
    label: "Shell",
    icon: Terminal,
    manifest: ["shell.exec"],
  },
  {
    value: "github",
    label: "GitHub",
    icon: GitBranch,
    manifest: ["github.push_branch", "github.read_repo"],
  },
  {
    value: "browser",
    label: "Browser",
    icon: Globe,
    manifest: ["browser.open_url", "browser.read_page"],
  },
];

const CONCERNS = [
  "Data exfiltration to external addresses",
  "Destructive shell commands",
  "Sensitive data in outbound mail",
  "Repository damage (force-push, deletes)",
  "Prompt injection from web pages",
  "Runaway cost or spending",
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

interface Answers {
  useCase: string;
  tools: string[];
  concerns: string[];
  risk: string;
  notes: string;
  name: string;
}

const initialAnswers: Answers = {
  useCase: "",
  tools: [],
  concerns: [],
  risk: "balanced",
  notes: "",
  name: "",
};

export default function OnboardPage() {
  const router = useRouter();
  const setDraftPolicy = useAppStore((s) => s.setDraftPolicy);
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState<Answers>(initialAnswers);

  const step = STEPS[stepIndex];

  const goNext = () =>
    setStepIndex((i) => Math.min(i + 1, STEPS.length - 1));
  const goBack = () => setStepIndex((i) => Math.max(i - 1, 0));

  const update = <K extends keyof Answers>(key: K, value: Answers[K]) =>
    setAnswers((a) => ({ ...a, [key]: value }));

  const composeIntent = () => {
    const useCaseLabel =
      USE_CASES.find((u) => u.value === answers.useCase)?.label ?? "agent";
    const toolLabels =
      answers.tools.length > 0
        ? answers.tools
            .map((t) => TOOLS.find((x) => x.value === t)?.label ?? t)
            .join(", ")
        : "various tools";
    const concernText =
      answers.concerns.length > 0
        ? answers.concerns.join("; ")
        : "general safety";
    const trimmed = answers.notes.trim();
    const trailing = trimmed ? ` Operator notes: ${trimmed}.` : "";
    return `This agent is a ${useCaseLabel}. It uses ${toolLabels}. Primary concerns: ${concernText}. Risk posture: ${answers.risk}.${trailing}`;
  };

  const composeManifest = () =>
    answers.tools.flatMap(
      (t) => TOOLS.find((x) => x.value === t)?.manifest ?? [],
    );

  const composeDomainHint = (): string | undefined => {
    switch (answers.useCase) {
      case "support":
      case "email":
        return "support";
      case "coding":
        return "engineering";
      case "research":
        return "research";
      default:
        return undefined;
    }
  };

  const mutation = useMutation({
    mutationFn: () =>
      generatePolicy({
        name: answers.name.trim(),
        user_intent: composeIntent(),
        tool_manifest: composeManifest(),
        domain_hint: composeDomainHint(),
      }),
    onSuccess: (result) => {
      setDraftPolicy({
        name: answers.name.trim(),
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
      name: answers.name.trim() || "Untitled policy",
      intent_summary: composeIntent(),
      judge_prompt: "",
      static_rules: [],
      notes: [],
      source: "manual",
    });
    router.push("/laws");
  };

  return (
    <main className="flex flex-1 items-center justify-center p-10">
      <div className="w-full max-w-4xl">
        <ProgressBar current={stepIndex} total={STEPS.length} label={step.label} />

        {step.key === "welcome" && <WelcomeStep onNext={goNext} />}
        {step.key === "tour" && (
          <TourStep onBack={goBack} onNext={goNext} />
        )}
        {step.key === "use-case" && (
          <UseCaseStep
            value={answers.useCase}
            onChange={(v) => update("useCase", v)}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {step.key === "tools" && (
          <ToolsStep
            value={answers.tools}
            onChange={(v) => update("tools", v)}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {step.key === "concerns" && (
          <ConcernsStep
            value={answers.concerns}
            onChange={(v) => update("concerns", v)}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {step.key === "risk" && (
          <RiskStep
            value={answers.risk}
            onChange={(v) => update("risk", v)}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {step.key === "notes" && (
          <NotesStep
            value={answers.notes}
            onChange={(v) => update("notes", v)}
            onBack={goBack}
            onNext={goNext}
          />
        )}
        {step.key === "name" && (
          <NameStep
            value={answers.name}
            onChange={(v) => update("name", v)}
            onBack={goBack}
            isPending={mutation.isPending}
            isError={mutation.isError}
            errorMessage={
              mutation.error instanceof Error
                ? mutation.error.message
                : undefined
            }
            onSubmit={() => mutation.mutate()}
            onEmptyDraft={createEmptyDraft}
          />
        )}
      </div>
    </main>
  );
}

function ProgressBar({
  current,
  total,
  label,
}: {
  current: number;
  total: number;
  label: string;
}) {
  return (
    <div className="mb-10">
      <div className="mb-3 flex items-center justify-between font-mono text-xs uppercase tracking-[0.22em] text-ink-soft">
        <span>
          Step{" "}
          <span className="text-ink">{String(current + 1).padStart(2, "0")}</span>{" "}
          of {String(total).padStart(2, "0")}
        </span>
        <span className="text-ink">{label}</span>
      </div>
      <div className="flex gap-1.5">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-1.5 flex-1 border border-ink/30",
              i <= current ? "bg-brass-dark" : "bg-parchment",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function StepShell({
  title,
  hint,
  required,
  children,
  footer,
}: {
  title: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <section className="border border-brass/40 bg-parchment p-10 shadow-[4px_4px_0_#2b1810] md:p-14">
      <div className="mb-2 flex items-center gap-3">
        <h2 className="font-heading text-4xl text-ink md:text-5xl">{title}</h2>
        {required && (
          <span className="font-mono text-[10px] uppercase tracking-widest text-wanted-red">
            required
          </span>
        )}
      </div>
      {hint && (
        <p className="mb-8 max-w-2xl text-base leading-relaxed text-ink-soft">
          {hint}
        </p>
      )}
      <div className="mb-10">{children}</div>
      <div className="flex items-center justify-between border-t border-brass/30 pt-6">
        {footer}
      </div>
    </section>
  );
}

function NavButton({
  children,
  onClick,
  variant = "ghost",
  disabled,
  type = "button",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  if (variant === "primary") {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        className="border border-ink bg-brass-dark px-8 py-3 text-base font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
      >
        {children}
      </button>
    );
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="font-mono text-xs uppercase tracking-widest text-ink-soft underline-offset-4 transition hover:text-ink hover:underline disabled:opacity-50"
    >
      {children}
    </button>
  );
}

function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <section className="border border-brass/40 bg-parchment p-12 text-center shadow-[4px_4px_0_#2b1810] md:p-16">
      <div className="mb-8 flex justify-center text-brass-dark">
        <svg width="96" height="96" aria-hidden>
          <use href="#sheriff-star" />
        </svg>
      </div>
      <h1 className="font-heading text-5xl leading-tight text-ink md:text-7xl">
        You are the Sheriff now
      </h1>
      <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-ink">
        Every AI agent that wants to run a tool (send an email, push code,
        open a browser) now has to come through your office first. You set
        the laws. AgentSheriff enforces them.
      </p>
      <p className="mx-auto mt-5 max-w-xl text-base text-ink-soft">
        Eight quick steps: a welcome, a tour of the office, then a few
        questions so we can draft a starter policy.
      </p>
      <div className="mt-10">
        <NavButton variant="primary" onClick={onNext}>
          Begin →
        </NavButton>
      </div>
    </section>
  );
}

function TourStep({
  onBack,
  onNext,
}: {
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <StepShell
      title="Tour the office"
      hint="Every surface you will work with, and what lives there."
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton variant="primary" onClick={onNext}>
            Next →
          </NavButton>
        </>
      }
    >
      <div className="grid gap-3 md:grid-cols-2">
        {NAV_ROUTES.map((route) => {
          const Icon = NAV_ICON_MAP[route.icon] ?? Home;
          const desc = TAB_DESCRIPTIONS[route.href] ?? "";
          return (
            <div
              key={route.href}
              className="flex items-start gap-4 border border-brass/40 bg-parchment-deep/40 p-5"
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
    </StepShell>
  );
}

function UseCaseStep({
  value,
  onChange,
  onBack,
  onNext,
}: {
  value: string;
  onChange: (v: string) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <StepShell
      title="What is this agent for?"
      hint="Pick the closest match. Drives a few default rules and a domain hint to the judge."
      required
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton variant="primary" onClick={onNext} disabled={!value}>
            Next →
          </NavButton>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {USE_CASES.map((opt) => {
          const Icon = opt.icon;
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={cn(
                "flex h-full flex-col items-start gap-3 border p-6 text-left transition",
                selected
                  ? "border-ink bg-brass-dark text-parchment shadow-[4px_4px_0_#2b1810]"
                  : "border-ink/40 bg-parchment text-ink hover:border-ink hover:shadow-[3px_3px_0_#2b1810]",
              )}
            >
              <Icon
                className={cn(
                  "h-8 w-8",
                  selected ? "text-parchment" : "text-brass-dark",
                )}
              />
              <span className="font-heading text-2xl leading-tight">
                {opt.label}
              </span>
              <span
                className={cn(
                  "text-sm leading-relaxed",
                  selected ? "text-parchment/80" : "text-ink-soft",
                )}
              >
                {opt.summary}
              </span>
            </button>
          );
        })}
      </div>
    </StepShell>
  );
}

function ToolsStep({
  value,
  onChange,
  onBack,
  onNext,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const toggle = (v: string) =>
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  return (
    <StepShell
      title="Which tools will it use?"
      hint="Pick all that apply. Each tool you select gets included in the policy's tool manifest."
      required
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton
            variant="primary"
            onClick={onNext}
            disabled={value.length === 0}
          >
            Next →
          </NavButton>
        </>
      }
    >
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {TOOLS.map((t) => {
          const Icon = t.icon;
          const selected = value.includes(t.value);
          return (
            <button
              key={t.value}
              type="button"
              onClick={() => toggle(t.value)}
              className={cn(
                "flex items-center gap-4 border p-5 text-left transition",
                selected
                  ? "border-ink bg-brass-dark text-parchment shadow-[4px_4px_0_#2b1810]"
                  : "border-ink/40 bg-parchment text-ink hover:border-ink hover:shadow-[3px_3px_0_#2b1810]",
              )}
            >
              <Icon
                className={cn(
                  "h-7 w-7",
                  selected ? "text-parchment" : "text-brass-dark",
                )}
              />
              <span className="font-heading text-2xl">{t.label}</span>
              {selected && (
                <span className="ml-auto font-mono text-xs uppercase tracking-widest">
                  ✓ on
                </span>
              )}
            </button>
          );
        })}
      </div>
      <p className="mt-4 font-mono text-[11px] uppercase tracking-widest text-ink-soft">
        {value.length} selected
      </p>
    </StepShell>
  );
}

function ConcernsStep({
  value,
  onChange,
  onBack,
  onNext,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const toggle = (v: string) =>
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  return (
    <StepShell
      title="What worries you most?"
      hint="Optional. Pick any that apply. The judge will weigh these heavier when calls get borderline."
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton variant="primary" onClick={onNext}>
            Next →
          </NavButton>
        </>
      }
    >
      <div className="grid gap-3 md:grid-cols-2">
        {CONCERNS.map((c) => {
          const selected = value.includes(c);
          return (
            <button
              key={c}
              type="button"
              onClick={() => toggle(c)}
              className={cn(
                "border p-4 text-left transition",
                selected
                  ? "border-ink bg-brass-dark text-parchment shadow-[3px_3px_0_#2b1810]"
                  : "border-ink/40 bg-parchment text-ink hover:border-ink",
              )}
            >
              <span className="font-heading text-lg leading-snug">{c}</span>
              {selected && (
                <span className="mt-1 block font-mono text-[10px] uppercase tracking-widest opacity-80">
                  ✓ flagged
                </span>
              )}
            </button>
          );
        })}
      </div>
    </StepShell>
  );
}

function RiskStep({
  value,
  onChange,
  onBack,
  onNext,
}: {
  value: string;
  onChange: (v: string) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <StepShell
      title="How strict should the Sheriff be?"
      hint="Sets the default disposition for calls that don't match a static rule."
      required
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton variant="primary" onClick={onNext} disabled={!value}>
            Next →
          </NavButton>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-3">
        {RISK_OPTIONS.map((opt) => {
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={cn(
                "flex flex-col items-start gap-3 border p-6 text-left transition",
                selected
                  ? "border-ink bg-brass-dark text-parchment shadow-[4px_4px_0_#2b1810]"
                  : "border-ink/40 bg-parchment text-ink hover:border-ink hover:shadow-[3px_3px_0_#2b1810]",
              )}
            >
              <span className="font-heading text-3xl leading-none">
                {opt.label}
              </span>
              <span
                className={cn(
                  "text-sm leading-relaxed",
                  selected ? "text-parchment/80" : "text-ink-soft",
                )}
              >
                {opt.hint}
              </span>
            </button>
          );
        })}
      </div>
    </StepShell>
  );
}

function NotesStep({
  value,
  onChange,
  onBack,
  onNext,
}: {
  value: string;
  onChange: (v: string) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <StepShell
      title="Anything else we should know?"
      hint="Optional. Anything you write here gets added to the policy intent and shown to the judge."
      footer={
        <>
          <NavButton onClick={onBack}>← Back</NavButton>
          <NavButton variant="primary" onClick={onNext}>
            Next →
          </NavButton>
        </>
      }
    >
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={6}
        placeholder="e.g. Only send mail to addresses ending in @acme.com. Never push to the main branch."
        className="w-full border border-ink/40 bg-parchment-deep/40 px-5 py-4 text-lg text-ink transition focus:border-ink focus:outline-none focus:ring-2 focus:ring-brass/30"
      />
    </StepShell>
  );
}

function NameStep({
  value,
  onChange,
  onBack,
  isPending,
  isError,
  errorMessage,
  onSubmit,
  onEmptyDraft,
}: {
  value: string;
  onChange: (v: string) => void;
  onBack: () => void;
  isPending: boolean;
  isError: boolean;
  errorMessage?: string;
  onSubmit: () => void;
  onEmptyDraft: () => void;
}) {
  const canSubmit = value.trim().length > 0 && !isPending;
  return (
    <StepShell
      title="Save this policy as"
      hint="Shows up on every decision and in the Ledger. You can rename it later."
      required
      footer={
        <>
          <NavButton onClick={onBack} disabled={isPending}>
            ← Back
          </NavButton>
          <NavButton
            variant="primary"
            type="button"
            disabled={!canSubmit}
            onClick={onSubmit}
          >
            {isPending ? "Drafting…" : "Draft my policy →"}
          </NavButton>
        </>
      }
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Finance inbox assistant"
        className="w-full border border-ink/40 bg-parchment-deep/40 px-5 py-4 text-2xl font-heading text-ink transition focus:border-ink focus:outline-none focus:ring-2 focus:ring-brass/30"
        maxLength={80}
      />
      {isError && (
        <div className="mt-6 border-l-4 border-wanted-red bg-parchment-deep/60 p-4">
          <p className="font-heading text-base text-wanted-red">
            Could not reach the gateway
          </p>
          {errorMessage && (
            <p className="mt-1 text-sm text-ink-soft">{errorMessage}</p>
          )}
          <button
            type="button"
            onClick={onEmptyDraft}
            className="mt-3 text-sm text-wanted-red underline underline-offset-2 hover:opacity-80"
          >
            Start an empty draft instead →
          </button>
        </div>
      )}
    </StepShell>
  );
}
