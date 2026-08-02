/**
 * FE-S08-01 — thin Integrations Studio chrome (STORY-08-07 prep).
 * Steps are disabled; Hub HTTP is not live. No invented API clients.
 * Resume full Studio when BE Hub HTTP lands. Not Production GO.
 */

export const STUDIO_STEPS = [
  { id: "connect", label: "Connect" },
  { id: "test", label: "Test" },
  { id: "map", label: "Map" },
  { id: "schedule", label: "Schedule" },
  { id: "monitor", label: "Monitor" },
  { id: "disconnect", label: "Disconnect" },
] as const;

export function IntegrationsStudioShell() {
  return (
    <section
      className="space-y-3"
      data-testid="integrations-studio-shell"
      aria-label="Integrations Studio"
    >
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Integrations Studio (prep)
        </h2>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          STORY-08-07 flow chrome only. Actions stay disabled until Hub HTTP
          exists.
        </p>
      </div>

      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="integrations-studio-api-honesty"
      >
        Hub HTTP API not live. Connect/test/map/schedule/monitor/disconnect
        cannot call Backend yet (blocked on Hub HTTP + STORY-08-06). No invented
        endpoints. Not Production GO.
      </p>

      <ol
        className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
        data-testid="integrations-studio-steps"
      >
        {STUDIO_STEPS.map((step, index) => (
          <li key={step.id}>
            <button
              type="button"
              disabled
              data-testid={`integrations-studio-step-${step.id}`}
              className="flex w-full min-h-[44px] cursor-not-allowed items-center gap-2 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-2 text-left text-sm text-[var(--text-muted)] opacity-80"
              title="Hub HTTP API not live"
            >
              <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[var(--border-default)] text-xs">
                {index + 1}
              </span>
              <span>
                <span className="font-medium text-[var(--text-secondary)]">
                  {step.label}
                </span>
                <span className="mt-0.5 block text-xs">API not live</span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
