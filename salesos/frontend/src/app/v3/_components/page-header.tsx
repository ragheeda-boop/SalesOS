import type { ReactNode } from "react";

/**
 * v3 PageHeader — ensures every route has a visible h1 (a11y baseline).
 * Spike chrome only; not the full Design System PageHeader.
 */
export function PageHeader({
  title,
  description,
  actions,
  badge,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  badge?: ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1
            className="text-2xl font-semibold tracking-tight text-[var(--text-primary)]"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {title}
          </h1>
          {badge}
        </div>
        {description ? (
          <p className="text-sm text-[var(--text-secondary)]">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
