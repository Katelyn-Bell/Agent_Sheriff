import { PageHeader } from "@/components/PageHeader";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function TrialRecordDetailPage({ params }: PageProps) {
  const { id } = await params;
  return (
    <section>
      <PageHeader
        title={`Trial Record ${id}`}
        subtitle="Original vs. replayed decisions"
      />
      <p className="text-ink-soft">Disagreement detail coming in Run 4A.</p>
    </section>
  );
}
