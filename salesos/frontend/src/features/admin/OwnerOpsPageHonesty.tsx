/* eslint-disable custom-rules/no-tailwind-color-classes */
/**
 * FE-S07-07 — shared Owner Console ops-page honesty strip.
 * Audience enforcement stays BE; mint via /admin/login (DEC-093). Not Production GO.
 */
export type OwnerOpsSurface = "flags" | "config" | "audit";

const SURFACE_COPY: Record<OwnerOpsSurface, string> = {
  flags:
    "Feature flags require owner-audience admin APIs. Mutating rollouts is Ops-owned; tenant JWT 401s toast honesty and keep the session (FE-S07-06). Sign in at /admin/login for owner mint. Not Production GO.",
  config:
    "System config YAML requires owner-audience admin APIs. Validate before save; owner mint at /admin/login. Not Production GO.",
  audit:
    "Audit log is a read-path Ops surface. Export/filter still need owner audience. Sign in at /admin/login for owner mint. Not Production GO.",
};

export function OwnerOpsPageHonesty({ surface }: { surface: OwnerOpsSurface }) {
  return (
    <p
      className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
      data-testid={`owner-ops-${surface}-honesty`}
    >
      {SURFACE_COPY[surface]}
    </p>
  );
}
