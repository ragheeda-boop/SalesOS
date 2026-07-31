import type { ReactNode } from "react";

export type MetricCardItem = {
  label: string;
  value: ReactNode;
  hint?: string;
};

export function MetricCards({ items }: { items: MetricCardItem[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-3"
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.06em] text-[var(--text-muted)]">
            {item.label}
          </p>
          <p className="mt-2 text-lg font-semibold tracking-tight text-[var(--text-primary)]">
            {item.value}
          </p>
          {item.hint ? (
            <p className="mt-1 text-[12px] text-[var(--text-muted)]">
              {item.hint}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
