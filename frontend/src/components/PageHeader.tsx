import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-end justify-between gap-6 border-b border-brass/40 pb-5 mb-8",
        className,
      )}
    >
      <div>
        <h1 className="font-heading text-4xl leading-none text-ink">{title}</h1>
        {subtitle && (
          <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-soft">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex-shrink-0">{actions}</div>}
    </div>
  );
}
