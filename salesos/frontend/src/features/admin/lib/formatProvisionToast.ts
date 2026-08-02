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

/** FE-S04-28 — toast from TenantLifecycleResponse (suspend/activate/soft-delete). */
export function formatLifecycleResultDescription(result: {
  tenant_id: string;
  is_active?: boolean;
  provisioning_status?: string | null;
  prior_provisioning_status?: string | null;
  reason?: string;
}): string {
  const parts = [`tenant_id=${result.tenant_id}`];
  if (typeof result.is_active === "boolean") {
    parts.push(`is_active=${result.is_active}`);
  }
  if (result.prior_provisioning_status != null) {
    parts.push(`prior=${result.prior_provisioning_status || "unknown"}`);
  }
  parts.push(`provisioning=${result.provisioning_status || "pending"}`);
  const r = result.reason?.trim();
  if (r) parts.push(`reason=${r}`);
  return parts.join(" · ");
}

export function formatSuspendResultDescription(
  tenantId: string,
  reason?: string,
): string {
  return formatLifecycleResultDescription({
    tenant_id: tenantId,
    is_active: false,
    provisioning_status: "suspended",
    reason,
  });
}

/** FE-S04-27 — activate toast from POST /activate response. */
export function formatActivateResultDescription(result: {
  tenant_id: string;
  prior_provisioning_status?: string | null;
  provisioning_status?: string;
  reason?: string;
  is_active?: boolean;
}): string {
  return formatLifecycleResultDescription({
    ...result,
    is_active: result.is_active ?? true,
    provisioning_status: result.provisioning_status || "active",
  });
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

/** FE-S04-25 — list trial honesty badge. */
export function trialBadgeLabel(
  trialEndsAt: string | null | undefined,
  nowMs: number = Date.now(),
): string {
  const bucket = trialBucket(trialEndsAt, nowMs);
  if (bucket === "has_trial") return "Active trial";
  if (bucket === "expired") return "Expired";
  return "No trial";
}

export function trialBadgeVariant(
  trialEndsAt: string | null | undefined,
  nowMs: number = Date.now(),
): "success" | "warning" | "default" {
  const bucket = trialBucket(trialEndsAt, nowMs);
  if (bucket === "has_trial") return "success";
  if (bucket === "expired") return "warning";
  return "default";
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

/** FE-S04-29/33 — shareable Owner Console filter query (mirrors URL sync). */
export function buildAdminTenantsFilterQuery(filters: {
  search?: string;
  plan?: string;
  plan_id?: string;
  status?: string;
  provisioning_status?: string;
  region?: string;
  data_residency?: string;
  trial?: TrialFilter;
  sort?: TenantSortKey;
  page?: number;
  page_size?: number;
}): string {
  const params = new URLSearchParams();
  const search = filters.search?.trim();
  if (search) params.set("search", search);
  if (filters.plan) params.set("plan", filters.plan);
  const planId = filters.plan_id?.trim();
  if (planId) params.set("plan_id", planId);
  if (filters.status) params.set("status", filters.status);
  if (filters.provisioning_status)
    params.set("provisioning_status", filters.provisioning_status);
  const region = filters.region?.trim();
  if (region) params.set("region", region);
  const residency = filters.data_residency?.trim();
  if (residency) params.set("data_residency", residency);
  if (filters.trial) params.set("trial", filters.trial);
  if (filters.sort && filters.sort !== "created_desc")
    params.set("sort", filters.sort);
  if (filters.page && filters.page > 1)
    params.set("page", String(filters.page));
  if (filters.page_size && filters.page_size !== 20)
    params.set("page_size", String(filters.page_size));
  return params.toString();
}

/** STORY-04-04 / FE-S04-35 — default retention days (settings.tenant_deletion_retention_days). */
export const TENANT_DELETION_RETENTION_DAYS = 30;

/** Soft-delete stamps settings.deletion_requested_at (tip fd5af4d). */
export function getDeletionRequestedAt(
  settings: Record<string, unknown> | null | undefined,
): string | null {
  const raw = settings?.deletion_requested_at;
  return typeof raw === "string" && raw.trim() ? raw : null;
}

/** FE-S04-35 — Owner Console retention honesty copy. */
export function retentionHardDeleteDescription(options?: {
  deletionRequestedAt?: string | null;
  retentionDays?: number;
  isInactive?: boolean;
}): string {
  const days = options?.retentionDays ?? TENANT_DELETION_RETENTION_DAYS;
  const stamp = options?.deletionRequestedAt;
  if (stamp) {
    return `Retention: soft-delete stamped ${stamp}. Hard-delete blocked until ~${days} days elapse unless force_immediate=true.`;
  }
  if (options?.isInactive) {
    return `Retention: inactive tenants may carry a soft-delete stamp. Hard-delete waits ~${days} days after soft-delete unless force_immediate=true. Direct hard-delete (no stamp) is allowed with confirm.`;
  }
  return `Retention: soft-delete stamps deletion_requested_at; hard-delete waits ~${days} days unless force_immediate=true. Active tenants may hard-delete with confirm only.`;
}

/** FE-S04-34 — toast from TenantReprovisionResponse. */
export function formatReprovisionResultDescription(result: {
  tenant_id: string;
  slug: string;
  provisioning_status?: string;
  created?: boolean;
  idempotent?: boolean;
  roles_provisioned?: number;
  permissions_provisioned?: number;
}): string {
  const parts = [
    `tenant_id=${result.tenant_id}`,
    `slug=${result.slug}`,
    `provisioning=${result.provisioning_status || "pending"}`,
  ];
  if (typeof result.created === "boolean") {
    parts.push(`created=${result.created}`);
  }
  if (typeof result.idempotent === "boolean") {
    parts.push(`idempotent=${result.idempotent}`);
  }
  if (typeof result.roles_provisioned === "number")
    parts.push(`roles=${result.roles_provisioned}`);
  if (typeof result.permissions_provisioned === "number")
    parts.push(`permissions=${result.permissions_provisioned}`);
  return parts.join(" · ");
}

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
