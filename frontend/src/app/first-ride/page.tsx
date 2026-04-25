"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { generatePolicy } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store";

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

const DOMAIN_HINTS = [
  { value: "", label: "No specific domain" },
  { value: "finance", label: "Finance" },
  { value: "support", label: "Customer support" },
  { value: "engineering", label: "Engineering" },
  { value: "research", label: "Research" },
  { value: "other", label: "Other" },
];

const MIN_INTENT_CHARS = 20;

export default function FirstRidePage() {
  const router = useRouter();
  const setDraftPolicy = useAppStore((s) => s.setDraftPolicy);

  const [name, setName] = useState("");
  const [userIntent, setUserIntent] = useState("");
  const [domainHint, setDomainHint] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      generatePolicy({
        name: name.trim(),
        user_intent: userIntent.trim(),
        tool_manifest: DEFAULT_TOOL_MANIFEST,
        domain_hint: domainHint || undefined,
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

  const canSubmit =
    name.trim().length > 0 && userIntent.trim().length >= MIN_INTENT_CHARS;

  const createEmptyDraft = () => {
    setDraftPolicy({
      name: name.trim() || "Untitled policy",
      intent_summary: userIntent.trim(),
      judge_prompt: "",
      static_rules: [],
      notes: [],
      source: "manual",
    });
    router.push("/laws");
  };

  return (
    <section className="max-w-2xl">
      <PageHeader
        title="First Ride"
        subtitle="Describe your agent · we'll draft a starter policy"
      />

      <p className="mb-8 text-ink-soft">
        Tell us what the agent is for. We generate a starter bundle of static
        restrictions plus a judge prompt — you edit everything before
        publishing.
      </p>

      <form
        className="space-y-6"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit && !mutation.isPending) mutation.mutate();
        }}
      >
        <Field
          label="Policy name"
          hint="Shows up in the Ledger and on published versions."
        >
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Finance inbox assistant"
            className={inputClass}
            maxLength={80}
            required
          />
        </Field>

        <Field
          label="What does your agent do?"
          hint={`Minimum ${MIN_INTENT_CHARS} characters. More detail = better starter rules.`}
        >
          <textarea
            value={userIntent}
            onChange={(e) => setUserIntent(e.target.value)}
            rows={5}
            placeholder="I use this agent to triage my inbox, draft replies to customers, and send internal invoices to our accountant. It should never email anyone outside the company."
            className={inputClass}
            required
          />
          <div className="mt-1 text-right font-mono text-[10px] uppercase tracking-widest text-ink-soft">
            {userIntent.length} / {MIN_INTENT_CHARS}+ characters
          </div>
        </Field>

        <Field
          label="Domain hint"
          hint="Optional — nudges the starter rules toward a vertical."
        >
          <select
            value={domainHint}
            onChange={(e) => setDomainHint(e.target.value)}
            className={inputClass}
          >
            {DOMAIN_HINTS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </Field>

        {mutation.isError && (
          <div className="border-l-4 border-wanted-red bg-parchment-deep/60 p-4">
            <p className="font-heading text-base text-wanted-red">
              Couldn&apos;t reach the gateway
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

        <div className="flex items-center gap-4 pt-2">
          <button
            type="submit"
            disabled={!canSubmit || mutation.isPending}
            className="border border-ink bg-brass-dark px-5 py-2.5 font-semibold text-parchment transition hover:bg-brass disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Generating…" : "Generate starter policy"}
          </button>
          {!canSubmit && (
            <span className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
              Name + {MIN_INTENT_CHARS}-char intent required
            </span>
          )}
        </div>
      </form>
    </section>
  );
}

const inputClass =
  "w-full border border-ink/60 bg-parchment px-3 py-2 text-ink transition focus:border-brass focus:outline-none focus:ring-2 focus:ring-brass/30";

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
      <div className="mb-2 font-heading text-base text-ink">{label}</div>
      {hint && (
        <div className="mb-2 text-xs text-ink-soft">{hint}</div>
      )}
      {children}
    </label>
  );
}
