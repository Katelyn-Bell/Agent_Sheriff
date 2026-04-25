"use client";

import { ApprovalCard } from "@/components/ApprovalCard";
import { PageHeader } from "@/components/PageHeader";
import { selectPendingApprovals, useAppStore } from "@/lib/store";

export default function ApprovalsPage() {
  const pending = useAppStore(selectPendingApprovals);

  return (
    <section>
      <PageHeader
        title="Badge Approval"
        subtitle={
          pending.length === 0
            ? "No pending reviews"
            : `${pending.length} awaiting the sheriff`
        }
      />

      {pending.length === 0 ? (
        <div className="border border-dashed border-brass/50 bg-parchment-deep/40 p-10 text-center">
          <p className="font-heading text-xl text-ink">All quiet in town</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
            No pending approvals. Borderline tool calls will appear here
            automatically and wait for your decision.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {pending.map((a) => (
            <ApprovalCard key={a.id} approval={a} />
          ))}
        </div>
      )}
    </section>
  );
}
