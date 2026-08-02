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
