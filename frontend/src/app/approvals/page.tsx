import { PageHeader } from "@/components/PageHeader";

export default function ApprovalsPage() {
  return (
    <section>
      <PageHeader
        title="Badge Approval"
        subtitle="Pending human decisions"
      />
      <p className="text-ink-soft">Approval queue coming in Run 3B.</p>
    </section>
  );
}
