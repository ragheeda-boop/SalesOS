/**
 * FE-S08-01 / STORY-08-07 / FE-S08-08 — Studio step ids + Owner Console pointer.
 * Live Studio is IntegrationsStudio against Hub HTTP. Not Production GO.
 */

import Link from "next/link";

export const STUDIO_STEPS = [
  { id: "connect", label: "Connect" },
  { id: "test", label: "Test" },
  { id: "map", label: "Map" },
  { id: "conflict", label: "Conflict" },
  { id: "schedule", label: "Schedule" },
  { id: "monitor", label: "Monitor" },
  { id: "disconnect", label: "Disconnect" },
] as const;

/** Owner Console prep pointer — live flow is tenant `/integrations`. */
export function IntegrationsStudioShell() {
  return (
    <section
      className="space-y-3"
      data-testid="integrations-studio-shell"
      aria-label="Integrations Studio"
    >
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Integrations Studio
        </h2>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          STORY-08-07 / FE-S08-08 tenant Studio is live at{" "}
          <Link
            href="/integrations"
            className="underline"
            data-testid="integrations-studio-tenant-link"
          >
            /integrations
          </Link>
          .
        </p>
      </div>

      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="integrations-studio-api-honesty"
      >
        Hub HTTP is live on tip (STORY-08-06) including conflict-policy.
        OdooAdapter certify path landed (STORY-09-01). Owner Console inventory
        stays read-path; mutate Studio flow uses tenant JWT + DOM-021 at
        `/integrations`. Not Production GO.
      </p>

      <ol
        className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
        data-testid="integrations-studio-steps"
      >
        {STUDIO_STEPS.map((step, index) => (
          <li key={step.id}>
            <Link
              href={`/integrations?step=${step.id}`}
              data-testid={`integrations-studio-step-${step.id}`}
              className="flex w-full min-h-[44px] items-center gap-2 rounded border border-[var(--border-default)] px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            >
              <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[var(--border-default)] text-xs">
                {index + 1}
              </span>
              <span>
                <span className="font-medium text-[var(--text-primary)]">
                  {step.label}
                </span>
                <span className="mt-0.5 block text-xs">Open Studio</span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
