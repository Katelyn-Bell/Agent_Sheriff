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

type Step = "welcome" | "tour" | "tailor";

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
    summary: "Tell us in the notes below.",
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
        Three quick stops: a welcome, a tour of your office, then a few
        questions so we can draft a starter policy.
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
          const Icon = NAV_ICON_MAP[route.icon] ?? Home;
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

  const [useCase, setUseCase] = useState<string>("");
  const [tools, setTools] = useState<string[]>([]);
  const [concerns, setConcerns] = useState<string[]>([]);
  const [risk, setRisk] = useState<string>("balanced");
  const [notes, setNotes] = useState<string>("");
  const [name, setName] = useState<string>("");

  const toggle = (
    list: string[],
    setList: (next: string[]) => void,
    value: string,
  ) => {
    setList(
      list.includes(value) ? list.filter((v) => v !== value) : [...list, value],
    );
  };

  const composeIntent = () => {
    const useCaseLabel =
      USE_CASES.find((u) => u.value === useCase)?.label ?? "agent";
    const toolLabels =
      tools.length > 0
        ? tools
            .map((t) => TOOLS.find((x) => x.value === t)?.label ?? t)
            .join(", ")
        : "various tools";
    const concernText =
      concerns.length > 0 ? concerns.join("; ") : "general safety";
    const trimmedNotes = notes.trim();
    const trailing = trimmedNotes ? ` Operator notes: ${trimmedNotes}.` : "";
    return `This agent is a ${useCaseLabel}. It uses ${toolLabels}. Primary concerns: ${concernText}. Risk posture: ${risk}.${trailing}`;
  };

  const composeManifest = () => {
    if (tools.length === 0) {
      return TOOLS.flatMap((t) => t.manifest);
    }
    return tools.flatMap(
      (t) => TOOLS.find((x) => x.value === t)?.manifest ?? [],
    );
  };

  const composeDomainHint = (): string | undefined => {
    switch (useCase) {
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
        name: name.trim(),
        user_intent: composeIntent(),
        tool_manifest: composeManifest(),
        domain_hint: composeDomainHint(),
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
      intent_summary: composeIntent(),
      judge_prompt: "",
      static_rules: [],
      notes: [],
      source: "manual",
    });
    router.push("/laws");
  };

  const canSubmit =
    useCase.length > 0 &&
    tools.length > 0 &&
    name.trim().length > 0 &&
    !mutation.isPending;

  return (
    <section className="border border-brass/40 bg-parchment p-10 shadow-[4px_4px_0_#2b1810] md:p-14">
      <div className="text-center">
        <h2 className="font-heading text-5xl text-ink">Set the laws</h2>
        <p className="mx-auto mt-4 max-w-xl text-base text-ink-soft">
          Six quick questions. We turn the answers into a starter policy you
          can edit on the Laws page.
        </p>
      </div>

      <form
        className="mt-12 space-y-12"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) mutation.mutate();
        }}
      >
        <Question
          number="01"
          question="What is this agent for?"
          required
          satisfied={useCase.length > 0}
        >
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {USE_CASES.map((opt) => (
              <UseCaseCard
                key={opt.value}
                option={opt}
                selected={useCase === opt.value}
                onSelect={() => setUseCase(opt.value)}
              />
            ))}
          </div>
        </Question>

        <Question
          number="02"
          question="Which tools will it use?"
          hint="Pick all that apply. We use this to seed the tool manifest."
          required
          satisfied={tools.length > 0}
        >
          <div className="flex flex-wrap gap-2">
            {TOOLS.map((t) => (
              <Chip
                key={t.value}
                icon={t.icon}
                label={t.label}
                selected={tools.includes(t.value)}
                onClick={() => toggle(tools, setTools, t.value)}
              />
            ))}
          </div>
        </Question>

        <Question
          number="03"
          question="What worries you most?"
          hint="Optional. Tells the judge what to weigh more heavily."
          satisfied={concerns.length > 0}
        >
          <div className="flex flex-wrap gap-2">
            {CONCERNS.map((c) => (
              <Chip
                key={c}
                label={c}
                selected={concerns.includes(c)}
                onClick={() => toggle(concerns, setConcerns, c)}
              />
            ))}
          </div>
        </Question>

        <Question
          number="04"
          question="How strict should the Sheriff be?"
          required
          satisfied={risk.length > 0}
        >
          <div className="grid gap-3 md:grid-cols-3">
            {RISK_OPTIONS.map((opt) => (
              <RiskCard
                key={opt.value}
                option={opt}
                selected={risk === opt.value}
                onSelect={() => setRisk(opt.value)}
              />
            ))}
          </div>
        </Question>

        <Question
          number="05"
          question="Anything else we should know?"
          hint="Optional. Free-text notes get added to the policy intent."
          satisfied={notes.trim().length > 0}
        >
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="e.g. Only send mail to addresses ending in @acme.com."
            className="w-full border border-ink/40 bg-parchment-deep/40 px-4 py-3 text-base text-ink transition focus:border-ink focus:outline-none focus:ring-2 focus:ring-brass/30"
          />
        </Question>

        <Question
          number="06"
          question="Save this policy as"
          required
          satisfied={name.trim().length > 0}
        >
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Finance inbox assistant"
            className="w-full border border-ink/40 bg-parchment-deep/40 px-4 py-3 text-base text-ink transition focus:border-ink focus:outline-none focus:ring-2 focus:ring-brass/30"
            maxLength={80}
            required
          />
        </Question>

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

        <div className="flex items-center justify-between border-t border-brass/30 pt-8">
          <button
            type="button"
            onClick={onBack}
            className="font-mono text-xs uppercase tracking-widest text-ink-soft underline-offset-4 hover:text-ink hover:underline"
          >
            ← Back
          </button>
          <button
            type="submit"
            disabled={!canSubmit}
            className="border border-ink bg-brass-dark px-10 py-4 text-lg font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Generating…" : "Draft my policy →"}
          </button>
        </div>
      </form>
    </section>
  );
}

function Question({
  number,
  question,
  hint,
  required,
  satisfied,
  children,
}: {
  number: string;
  question: string;
  hint?: string;
  required?: boolean;
  satisfied?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-5 flex items-baseline gap-4">
        <span className="font-mono text-base text-brass-dark">{number}</span>
        <span className="text-brass-dark">✦</span>
        <h3 className="flex-1 font-heading text-2xl text-ink">{question}</h3>
        {required && !satisfied && (
          <span className="font-mono text-[10px] uppercase tracking-widest text-wanted-red">
            required
          </span>
        )}
      </div>
      {hint && (
        <p className="-mt-3 mb-4 pl-12 text-sm text-ink-soft">{hint}</p>
      )}
      <div className="pl-0 md:pl-12">{children}</div>
    </div>
  );
}

function UseCaseCard({
  option,
  selected,
  onSelect,
}: {
  option: UseCaseOption;
  selected: boolean;
  onSelect: () => void;
}) {
  const Icon = option.icon;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex h-full flex-col items-start gap-2 border p-4 text-left transition",
        selected
          ? "border-ink bg-brass-dark text-parchment shadow-[4px_4px_0_#2b1810]"
          : "border-ink/40 bg-parchment text-ink hover:border-ink hover:shadow-[3px_3px_0_#2b1810]",
      )}
    >
      <Icon
        className={cn(
          "h-6 w-6",
          selected ? "text-parchment" : "text-brass-dark",
        )}
      />
      <span className="font-heading text-lg leading-tight">{option.label}</span>
      <span
        className={cn(
          "text-xs leading-snug",
          selected ? "text-parchment/80" : "text-ink-soft",
        )}
      >
        {option.summary}
      </span>
    </button>
  );
}

function RiskCard({
  option,
  selected,
  onSelect,
}: {
  option: { value: string; label: string; hint: string };
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex flex-col items-start gap-2 border p-5 text-left transition",
        selected
          ? "border-ink bg-brass-dark text-parchment shadow-[4px_4px_0_#2b1810]"
          : "border-ink/40 bg-parchment text-ink hover:border-ink hover:shadow-[3px_3px_0_#2b1810]",
      )}
    >
      <span className="font-heading text-2xl leading-none">{option.label}</span>
      <span
        className={cn(
          "text-xs leading-relaxed",
          selected ? "text-parchment/80" : "text-ink-soft",
        )}
      >
        {option.hint}
      </span>
    </button>
  );
}

function Chip({
  icon,
  label,
  selected,
  onClick,
}: {
  icon?: LucideIcon;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  const Icon = icon;
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 border px-4 py-2 text-sm transition",
        selected
          ? "border-ink bg-brass-dark text-parchment shadow-[3px_3px_0_#2b1810]"
          : "border-ink/40 bg-parchment text-ink hover:border-ink",
      )}
    >
      {Icon && <Icon className="h-4 w-4" />}
      <span>{label}</span>
    </button>
  );
}
