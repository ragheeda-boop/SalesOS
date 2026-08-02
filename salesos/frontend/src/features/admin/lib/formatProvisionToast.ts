import type { AdminTenantDetail } from "@/lib/api";

/**
 * FE-S04-07 — surface Owner Platform / provision_workflow result fields in toast copy.
 * Create API returns TenantDetail (not full workflow dict); summarize available fields.
 */
export function formatProvisionResultDescription(
  tenant: Pick<
    AdminTenantDetail,
    | "slug"
    | "plan_id"
    | "region"
    | "data_residency"
    | "provisioning_status"
    | "trial_ends_at"
  >,
): string {
  const parts: string[] = [
    `slug=${tenant.slug}`,
    `provisioning=${tenant.provisioning_status || "pending"}`,
  ];
  if (tenant.plan_id) parts.push(`plan_id=${tenant.plan_id}`);
  if (tenant.region) parts.push(`region=${tenant.region}`);
  if (tenant.data_residency) parts.push(`residency=${tenant.data_residency}`);
  if (tenant.trial_ends_at) parts.push(`trial_ends=${tenant.trial_ends_at}`);
  return parts.join(" · ");
}

export function formatSuspendResultDescription(
  tenantId: string,
  reason?: string,
): string {
  const r = reason?.trim();
  return r
    ? `tenant_id=${tenantId} · reason=${r} · provisioning=suspended`
    : `tenant_id=${tenantId} · provisioning=suspended`;
}

/** FE-S04-13 — soft-delete inactive vs suspend (both may set is_active=false). */
export function activityStatusLabel(tenant: {
  is_active: boolean;
  provisioning_status?: string | null;
}): string {
  if (tenant.is_active) return "Active";
  if ((tenant.provisioning_status || "") === "suspended") return "Suspended";
  return "Inactive";
}

export type TrialFilter = "" | "has_trial" | "expired" | "none";

/** FE-S04-15 — classify trial_ends_at for list filter/column. */
export function trialBucket(
  trialEndsAt: string | null | undefined,
  nowMs: number = Date.now(),
): Exclude<TrialFilter, ""> {
  if (!trialEndsAt) return "none";
  const ends = Date.parse(trialEndsAt);
  if (Number.isNaN(ends)) return "none";
  return ends < nowMs ? "expired" : "has_trial";
}

export function formatTrialEndsLabel(
  trialEndsAt: string | null | undefined,
): string {
  if (!trialEndsAt) return "—";
  const ends = Date.parse(trialEndsAt);
  if (Number.isNaN(ends)) return "—";
  return new Date(ends).toLocaleDateString();
}

export function matchesTrialFilter(
  trialEndsAt: string | null | undefined,
  filter: TrialFilter,
  nowMs: number = Date.now(),
): boolean {
  if (!filter) return true;
  return trialBucket(trialEndsAt, nowMs) === filter;
}

/** FE-S04-17 — detail-panel lifecycle copy (soft-delete vs suspend). */
export function lifecycleStatusDescription(tenant: {
  is_active: boolean;
  provisioning_status?: string | null;
}): string {
  const label = activityStatusLabel(tenant);
  const prov = tenant.provisioning_status || "pending";
  if (label === "Active") {
    return `Active · provisioning=${prov}`;
  }
  if (label === "Suspended") {
    return `Suspended via /suspend · provisioning=suspended · Activate restores is_active`;
  }
  return `Inactive (soft-deleted) · is_active=false · provisioning=${prov} · Activate restores access`;
}

export type TenantSortKey =
  "created_desc" | "created_asc" | "name_asc" | "name_desc";

/** FE-S04-19 — client-side list sort. */
export function sortAdminTenants<
  T extends { name: string; created_at: string },
>(list: T[], sort: TenantSortKey): T[] {
  const next = [...list];
  next.sort((a, b) => {
    switch (sort) {
      case "created_asc":
        return Date.parse(a.created_at) - Date.parse(b.created_at);
      case "name_asc":
        return a.name.localeCompare(b.name);
      case "name_desc":
        return b.name.localeCompare(a.name);
      case "created_desc":
      default:
        return Date.parse(b.created_at) - Date.parse(a.created_at);
    }
  });
  return next;
}
