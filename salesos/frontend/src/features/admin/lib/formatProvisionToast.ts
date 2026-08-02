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
  deleted_at?: string | null;
  subscription_status?: string | null;
}): string {
  const parts = [`tenant_id=${result.tenant_id}`];
  if (typeof result.is_active === "boolean") {
    parts.push(`is_active=${result.is_active}`);
  }
  if (result.prior_provisioning_status != null) {
    parts.push(`prior=${result.prior_provisioning_status || "unknown"}`);
  }
  parts.push(`provisioning=${result.provisioning_status || "pending"}`);
  if (result.deleted_at) parts.push(`deleted_at=${result.deleted_at}`);
  if (result.subscription_status) {
    parts.push(`subscription=${result.subscription_status}`);
  }
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

/** Soft-delete may dual-write settings.deletion_requested_at (tip fd5af4d). */
export function getDeletionRequestedAt(
  settings: Record<string, unknown> | null | undefined,
): string | null {
  const raw = settings?.deletion_requested_at;
  return typeof raw === "string" && raw.trim() ? raw : null;
}

export function resolveTenantDeletedAt(tenant: {
  deleted_at?: string | null;
  settings?: Record<string, unknown> | null;
}): string | null {
  const col = tenant.deleted_at;
  if (typeof col === "string" && col.trim()) return col;
  return getDeletionRequestedAt(tenant.settings);
}

export function retentionDaysRemaining(
  deletedAt: string | null | undefined,
  retentionDays: number = TENANT_DELETION_RETENTION_DAYS,
  nowMs: number = Date.now(),
): number | null {
  if (!deletedAt) return null;
  const start = Date.parse(deletedAt);
  if (Number.isNaN(start)) return null;
  const end = start + retentionDays * 86_400_000;
  return Math.max(0, Math.ceil((end - nowMs) / 86_400_000));
}

export function retentionHardDeleteDescription(options?: {
  deletionRequestedAt?: string | null;
  retentionDays?: number;
  isInactive?: boolean;
}): string {
  const days = options?.retentionDays ?? TENANT_DELETION_RETENTION_DAYS;
  const stamp = options?.deletionRequestedAt;
  if (stamp) {
    const remaining = retentionDaysRemaining(stamp, days);
    const remainingPart = remaining == null ? "" : ` ~${remaining}d remaining.`;
    return `Retention: soft-delete stamped ${stamp} (tenants.deleted_at). Hard-delete blocked until ~${days} days elapse unless force_immediate=true.${remainingPart}`;
  }
  if (options?.isInactive) {
    return `Retention: inactive tenants may carry tenants.deleted_at. Hard-delete waits ~${days} days after soft-delete unless force_immediate=true. Direct hard-delete (no stamp) is allowed with confirm.`;
  }
  return `Retention: soft-delete stamps tenants.deleted_at (+ settings dual-write); hard-delete waits ~${days} days unless force_immediate=true. Active tenants may hard-delete with confirm only.`;
}

export function formatSubscriptionSummary(sub: {
  status: string;
  billing_cycle?: string | null;
  plan_id?: string | null;
  seats?: number | null;
  current_period_end?: string | null;
  pending_plan_id?: string | null;
  pending_effective_at?: string | null;
}): string {
  const parts = [`status=${sub.status}`];
  if (sub.billing_cycle) parts.push(`cycle=${sub.billing_cycle}`);
  if (sub.plan_id) parts.push(`plan_id=${sub.plan_id}`);
  if (typeof sub.seats === "number") parts.push(`seats=${sub.seats}`);
  if (sub.current_period_end) {
    parts.push(`period_end=${sub.current_period_end}`);
  }
  if (sub.pending_plan_id) {
    parts.push(`pending_plan=${sub.pending_plan_id}`);
  }
  if (sub.pending_effective_at) {
    parts.push(`pending_at=${sub.pending_effective_at}`);
  }
  return parts.join(" · ");
}

export function formatUsageMeterRow(meter: {
  metric_key: string;
  quantity: number;
  period_start?: string | null;
  period_end?: string | null;
}): string {
  const start = meter.period_start
    ? new Date(meter.period_start).toLocaleString()
    : "—";
  const end = meter.period_end
    ? new Date(meter.period_end).toLocaleString()
    : "—";
  return `${meter.metric_key}=${meter.quantity} · ${start} – ${end}`;
}

export function getApiErrorStatus(err: unknown): number | null {
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as { response?: { status?: unknown } }).response?.status ===
      "number"
  ) {
    return (err as { response: { status: number } }).response.status;
  }
  return null;
}

export function getApiErrorDetail(err: unknown): string | null {
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as { response?: { data?: { detail?: unknown } } }).response
      ?.data?.detail === "string"
  ) {
    return (err as { response: { data: { detail: string } } }).response.data
      .detail;
  }
  return null;
}

export function isStripeBillingUnavailableError(err: unknown): boolean {
  if (getApiErrorStatus(err) === 503) return true;
  const detail = getApiErrorDetail(err) || "";
  return detail.includes("STRIPE_SECRET_KEY");
}

export function stripeBillingUnavailableDescription(
  detail?: string | null,
): string {
  if (detail && detail.trim()) return detail.trim();
  return (
    "Stripe billing unavailable: STRIPE_SECRET_KEY not configured " +
    "(503 fail-closed). No invented keys — set real env secrets in ops."
  );
}

export function catalogPriceIdForCycle(
  item: {
    stripe_price_id_monthly?: string | null;
    stripe_price_id_yearly?: string | null;
  },
  cycle: "monthly" | "yearly",
): string | null {
  const raw =
    cycle === "yearly"
      ? item.stripe_price_id_yearly
      : item.stripe_price_id_monthly;
  return typeof raw === "string" && raw.trim() ? raw.trim() : null;
}

export const ADMIN_USAGE_METRIC_OPTIONS = [
  { label: "All metrics", value: "" },
  { label: "seats", value: "seats" },
  { label: "ai_tokens", value: "ai_tokens" },
  { label: "connector_syncs", value: "connector_syncs" },
  { label: "api_calls", value: "api_calls" },
  { label: "storage_mb", value: "storage_mb" },
] as const;

export function dunningGraceDaysRemaining(
  graceEndsAt: string | null | undefined,
  nowMs: number = Date.now(),
): number | null {
  if (!graceEndsAt) return null;
  const end = Date.parse(graceEndsAt);
  if (Number.isNaN(end)) return null;
  return Math.ceil((end - nowMs) / 86_400_000);
}

export function formatDunningCaseRow(c: {
  status: string;
  failure_count?: number;
  grace_ends_at?: string | null;
  last_stripe_invoice_id?: string | null;
}): string {
  const remaining = dunningGraceDaysRemaining(c.grace_ends_at);
  const grace =
    remaining == null
      ? ""
      : remaining >= 0
        ? ` · grace ~${remaining}d left`
        : ` · grace elapsed ${Math.abs(remaining)}d ago`;
  const inv = c.last_stripe_invoice_id
    ? ` · inv=${c.last_stripe_invoice_id}`
    : "";
  const fails =
    typeof c.failure_count === "number" ? ` · fails=${c.failure_count}` : "";
  return `status=${c.status}${fails}${grace}${inv}`;
}

export const ADMIN_DUNNING_STATUS_OPTIONS = [
  { label: "All statuses", value: "" },
  { label: "open", value: "open" },
  { label: "suspended", value: "suspended" },
  { label: "cleared", value: "cleared" },
] as const;

/** FE-S05-06 — pending plan honesty from subscription or quote. */
export function formatPendingPlanHonesty(sub: {
  pending_plan_id?: string | null;
  pending_effective_at?: string | null;
  plan_id?: string | null;
}): string | null {
  if (!sub.pending_plan_id) return null;
  const when = sub.pending_effective_at
    ? ` effective ${sub.pending_effective_at}`
    : " (period-end pending)";
  return `Pending plan change: ${sub.plan_id || "current"} → ${sub.pending_plan_id}${when}. Downgrades defer unless downgrade_immediate.`;
}

export function formatPlanChangeQuote(q: {
  direction: string;
  timing: string;
  amount_due_now: number;
  from_plan_id?: string | null;
  to_plan_id: string;
  remaining_fraction?: number;
  applied?: string | null;
  pending_plan_id?: string | null;
  pending_effective_at?: string | null;
}): string {
  const parts = [
    `direction=${q.direction}`,
    `timing=${q.timing}`,
    `due_now=${q.amount_due_now}`,
    `from=${q.from_plan_id || "—"}`,
    `to=${q.to_plan_id}`,
  ];
  if (typeof q.remaining_fraction === "number") {
    parts.push(`remain=${q.remaining_fraction}`);
  }
  if (q.applied) parts.push(`applied=${q.applied}`);
  if (q.pending_plan_id) parts.push(`pending=${q.pending_plan_id}`);
  if (q.pending_effective_at)
    parts.push(`pending_at=${q.pending_effective_at}`);
  return parts.join(" · ");
}

/** FE-S04-38 — STORY-04-03 suspended tenants are write-blocked (tenant API). */
export function suspendedWriteBlockDescription(tenant: {
  provisioning_status?: string | null;
}): string | null {
  if ((tenant.provisioning_status || "") !== "suspended") return null;
  return (
    "Suspended (STORY-04-03): tenant API writes are blocked (read-only). " +
    "Owner Console /activate restores writes. Admin Owner paths remain available."
  );
}

/** FE-S04-40 — safe default reprovision (failed/pending). */
export function canRetryReprovision(
  provisioningStatus?: string | null,
): boolean {
  const s = provisioningStatus || "";
  return s === "failed" || s === "pending";
}

/** FE-S04-41 — suspended needs force_active=true on /reprovision. */
export function requiresForceActiveReprovision(
  provisioningStatus?: string | null,
): boolean {
  return (provisioningStatus || "") === "suspended";
}

/** FE-S04-44 — usage period honesty. */
export function formatTenantUsagePeriod(usage: {
  period_start?: string | null;
  period_end?: string | null;
}): string {
  const start = usage.period_start
    ? new Date(usage.period_start).toLocaleDateString()
    : "—";
  const end = usage.period_end
    ? new Date(usage.period_end).toLocaleDateString()
    : "—";
  return `Period ${start} – ${end}`;
}

export const ADMIN_TENANTS_PAGE_SIZES = [20, 50, 100] as const;
export type AdminTenantsPageSize = (typeof ADMIN_TENANTS_PAGE_SIZES)[number];

export function parseAdminTenantsPageSize(
  value: string | null | undefined,
): AdminTenantsPageSize {
  const n = Number(value);
  return (ADMIN_TENANTS_PAGE_SIZES as readonly number[]).includes(n)
    ? (n as AdminTenantsPageSize)
    : 20;
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

/** FE-S06-02 — short honesty summary of Plan.entitlements. */
export function formatPlanEntitlementsSummary(
  ents:
    | {
        domains?: Record<string, { enabled?: boolean } | null> | null;
        quotas?: {
          seats?: number;
          ai_tokens_monthly?: number;
          connectors?: number;
          storage_mb?: number;
          api_calls_monthly?: number;
          ai_tokens_unlimited?: boolean;
          connectors_unlimited?: boolean;
        } | null;
        deployment_tier?: string | null;
        support_sla?: string | null;
        version?: number | null;
      }
    | null
    | undefined,
): string {
  if (!ents) return "entitlements=(tier default / unset)";
  const domains = ents.domains || {};
  const enabled = Object.entries(domains).filter(([, d]) => d && d.enabled);
  const q = ents.quotas;
  const seats = q?.seats ?? "—";
  const ai = q?.ai_tokens_unlimited
    ? "ai=unlimited"
    : `ai=${q?.ai_tokens_monthly ?? "—"}`;
  const conn = q?.connectors_unlimited
    ? "connectors=unlimited"
    : `connectors=${q?.connectors ?? "—"}`;
  return (
    `v${ents.version ?? 1} · domains_enabled=${enabled.length}/${Object.keys(domains).length}` +
    ` · seats=${seats} · ${ai} · ${conn}` +
    ` · storage_mb=${q?.storage_mb ?? "—"}` +
    ` · deploy=${ents.deployment_tier || "pooled"}` +
    ` · sla=${ents.support_sla || "community"}`
  );
}

export function parsePlanEntitlementsJson(
  raw: string,
):
  | { ok: true; value: Record<string, unknown> | null }
  | { ok: false; error: string } {
  const trimmed = raw.trim();
  if (!trimmed) return { ok: true, value: null };
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (parsed === null) return { ok: true, value: null };
    if (typeof parsed !== "object" || Array.isArray(parsed)) {
      return { ok: false, error: "entitlements must be a JSON object" };
    }
    return { ok: true, value: parsed as Record<string, unknown> };
  } catch (e: unknown) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "invalid JSON",
    };
  }
}

/** FE-S05-02c — honesty banner from GET /billing/stripe/status booleans. */
export function formatStripeStatusBanner(
  status:
    | {
        secret_key_configured?: boolean;
        webhook_secret_configured?: boolean;
        publishable_key_configured?: boolean;
        checkout_ready?: boolean;
        webhook_ready?: boolean;
        sandbox_soak_ready?: boolean;
        production_billing?: boolean;
        production_go?: boolean;
        honesty?: string | null;
      }
    | null
    | undefined,
): string {
  if (!status) return "Stripe status unavailable.";
  const flags = [
    `secret=${status.secret_key_configured ? "yes" : "no"}`,
    `webhook_secret=${status.webhook_secret_configured ? "yes" : "no"}`,
    `publishable=${status.publishable_key_configured ? "yes" : "no"}`,
    `checkout_ready=${status.checkout_ready ? "yes" : "no"}`,
    `webhook_ready=${status.webhook_ready ? "yes" : "no"}`,
    `sandbox_soak=${status.sandbox_soak_ready ? "yes" : "no"}`,
    `production_billing=${status.production_billing ? "yes" : "no"}`,
    `production_go=${status.production_go ? "yes" : "no"}`,
  ];
  const honesty =
    status.honesty ||
    "env-only secrets; empty STRIPE_* fail-closed 503. No invented keys.";
  return `${flags.join(" · ")}. ${honesty}`;
}

export function stripeStatusTone(
  status:
    | {
        checkout_ready?: boolean;
        sandbox_soak_ready?: boolean;
        production_go?: boolean;
      }
    | null
    | undefined,
): "ok" | "warn" | "blocked" {
  if (!status) return "blocked";
  if (status.production_go) return "ok"; // never true on tip honesty
  if (status.checkout_ready || status.sandbox_soak_ready) return "warn";
  return "blocked";
}

/** FE-S06-03 — Owner honesty for entitlements resolved from Owner plans list. */
export function formatResolvedPlanEntitlementsHonesty(options: {
  planId?: string | null;
  planName?: string | null;
  tier?: string | null;
  entitlements?: Parameters<typeof formatPlanEntitlementsSummary>[0];
  pendingPlanId?: string | null;
}): string {
  const plan = options.planId || "unset";
  const name = options.planName || "unknown";
  const tier = options.tier || "unknown";
  const summary = formatPlanEntitlementsSummary(options.entitlements);
  const pending = options.pendingPlanId
    ? ` Pending plan ${options.pendingPlanId} not yet effective for gates.`
    : "";
  return (
    `Resolved entitlements from plan ${name} (${tier} · id=${plan}): ${summary}.` +
    ` Enforced by BE middleware on gated DOM paths.` +
    pending +
    ` Not Production GO.`
  );
}

export function listDisabledEntitlementDomains(
  ents:
    | {
        domains?: Record<string, { enabled?: boolean } | null> | null;
      }
    | null
    | undefined,
): string[] {
  if (!ents?.domains) return [];
  return Object.entries(ents.domains)
    .filter(([, d]) => !d || !d.enabled)
    .map(([k]) => k)
    .sort();
}

export {
  ENTITLEMENT_DENIED_EVENT,
  formatEntitlementDeniedMessage,
  getEntitlementDeniedFromError,
  isEntitlementDeniedPayload,
  type EntitlementDeniedPayload,
} from "@/lib/api/entitlementErrors";
