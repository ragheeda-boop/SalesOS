"use client";

import { useCallback, useMemo, useState } from "react";
import { Button, Input, Select, Spinner, useToast } from "@salesos/ui";
import {
  useAdminBillingCatalog,
  useAdminPlatformInvoices,
  useAdminTenantSubscription,
  useAdminUsageMeters,
  useCreateAdminStripeCheckoutSession,
  useCreateAdminStripePortalSession,
  useRollupAdminUsage,
} from "@/lib/hooks/adminQueries";
import {
  ADMIN_USAGE_METRIC_OPTIONS,
  catalogPriceIdForCycle,
  formatSubscriptionSummary,
  formatUsageMeterRow,
  getApiErrorDetail,
  isStripeBillingUnavailableError,
  stripeBillingUnavailableDescription,
} from "@/features/admin/lib/formatProvisionToast";

type BillingCycle = "monthly" | "yearly";

/**
 * FE-S05-01..04 — Owner Console billing + UsageMeter against tip 0a5f198.
 * Catalog / Checkout / Portal / platform invoices / usage meters.
 * Honest 503 empty-states. No invented Stripe keys. Not Production GO.
 */
export function TenantBillingPanel({ tenantId }: { tenantId: string }) {
  const { toast } = useToast();
  const {
    data: subscription,
    isLoading: subscriptionLoading,
    isError: subscriptionError,
    error: subscriptionErr,
  } = useAdminTenantSubscription(tenantId);
  const {
    data: catalog,
    isLoading: catalogLoading,
    isError: catalogError,
    error: catalogErr,
  } = useAdminBillingCatalog(true);
  const {
    data: invoices,
    isLoading: invoicesLoading,
    isError: invoicesError,
    error: invoicesErr,
  } = useAdminPlatformInvoices(tenantId);
  const [metricFilter, setMetricFilter] = useState("");
  const {
    data: usageMeters,
    isLoading: usageLoading,
    isError: usageError,
    error: usageErr,
    refetch: refetchUsage,
  } = useAdminUsageMeters(tenantId, metricFilter || undefined);
  const checkoutMutation = useCreateAdminStripeCheckoutSession();
  const portalMutation = useCreateAdminStripePortalSession();
  const rollupMutation = useRollupAdminUsage();

  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly");
  const [manualPriceId, setManualPriceId] = useState("");
  const [billingUnavailableDetail, setBillingUnavailableDetail] = useState<
    string | null
  >(null);

  const planOptions = useMemo(
    () =>
      (catalog || []).map((p) => ({
        label: `${p.name} (${p.tier})`,
        value: p.id,
      })),
    [catalog],
  );

  const selectedPlan = useMemo(
    () => (catalog || []).find((p) => p.id === selectedPlanId) || null,
    [catalog, selectedPlanId],
  );

  const resolvedCatalogPrice = selectedPlan
    ? catalogPriceIdForCycle(selectedPlan, billingCycle)
    : null;

  const markUnavailable = useCallback(
    (err: unknown) => {
      const detail = stripeBillingUnavailableDescription(getApiErrorDetail(err));
      setBillingUnavailableDetail(detail);
      toast({
        variant: "error",
        title: "Billing unavailable",
        description: detail,
      });
    },
    [toast],
  );

  const handleCheckout = useCallback(async () => {
    const priceOverride = manualPriceId.trim();
    if (!priceOverride && !selectedPlanId) {
      toast({
        variant: "error",
        title: "Select a catalog plan or paste price_id",
        description:
          "Use catalog Stripe Price ids from ops, or paste a real price_…. No invented keys.",
      });
      return;
    }
    if (!priceOverride && selectedPlan && !resolvedCatalogPrice) {
      toast({
        variant: "error",
        title: "Plan missing Stripe Price id",
        description: `plan has no stripe_price_id_${billingCycle} configured (ops binds real ids).`,
      });
      return;
    }
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const returnBase = `${origin}/admin/tenants?checkout=`;
    try {
      const result = await checkoutMutation.mutateAsync({
        tenant_id: tenantId,
        mode: "subscription",
        billing_cycle: billingCycle,
        success_url: `${returnBase}success`,
        cancel_url: `${returnBase}cancel`,
        ...(priceOverride
          ? { price_id: priceOverride }
          : { plan_id: selectedPlanId }),
      });
      setBillingUnavailableDetail(null);
      if (result.url) {
        window.location.assign(result.url);
        return;
      }
      toast({
        variant: "error",
        title: "Checkout Session missing URL",
        description: result.id ? `session=${result.id}` : "No checkout URL",
      });
    } catch (err: unknown) {
      if (isStripeBillingUnavailableError(err)) {
        markUnavailable(err);
        return;
      }
      toast({
        variant: "error",
        title: "Checkout Session failed",
        description:
          getApiErrorDetail(err) || "Stripe Checkout Session create failed",
      });
    }
  }, [
    manualPriceId,
    selectedPlanId,
    selectedPlan,
    resolvedCatalogPrice,
    billingCycle,
    checkoutMutation,
    tenantId,
    toast,
    markUnavailable,
  ]);

  const handlePortal = useCallback(async () => {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    try {
      const result = await portalMutation.mutateAsync({
        tenant_id: tenantId,
        return_url: `${origin}/admin/tenants`,
      });
      setBillingUnavailableDetail(null);
      if (result.url) {
        window.location.assign(result.url);
        return;
      }
      toast({
        variant: "error",
        title: "Portal Session missing URL",
        description: result.id ? `session=${result.id}` : "No portal URL",
      });
    } catch (err: unknown) {
      if (isStripeBillingUnavailableError(err)) {
        markUnavailable(err);
        return;
      }
      const status =
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as { response?: { status?: unknown } }).response?.status ===
          "number"
          ? (err as { response: { status: number } }).response.status
          : null;
      toast({
        variant: "error",
        title:
          status === 409
            ? "Portal needs Checkout first"
            : "Portal Session failed",
        description:
          getApiErrorDetail(err) ||
          "Complete Checkout so stripe_customer_id exists",
      });
    }
  }, [portalMutation, tenantId, toast, markUnavailable]);

  const handleRollup = useCallback(async () => {
    try {
      const result = await rollupMutation.mutateAsync({});
      await refetchUsage();
      toast({
        variant: "success",
        title: "Usage rollup complete",
        description: Object.entries(result)
          .map(([k, v]) => `${k}=${String(v)}`)
          .join(" · "),
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Usage rollup failed",
        description: getApiErrorDetail(err) || "rollup failed",
      });
    }
  }, [rollupMutation, refetchUsage, toast]);

  return (
    <div
      className="space-y-3 rounded-lg border border-[var(--border-default)] p-4"
      data-testid="admin-tenants-billing"
    >
      <div>
        <p className="font-medium text-[var(--text-primary)]">
          Billing / usage
        </p>
        <p className="text-xs text-[var(--text-muted)]">
          STORY-05-01/02/02b/03 — catalog, Checkout, Portal, platform invoices,
          UsageMeter. Stripe paths fail-closed without secrets. No invented
          keys. Not Production GO.
        </p>
      </div>

      <div data-testid="admin-tenants-subscription">
        {subscriptionLoading ? (
          <p className="text-sm text-[var(--text-muted)]">
            Loading subscription…
          </p>
        ) : subscription ? (
          <p
            className="text-sm text-[var(--text-secondary)]"
            data-testid="admin-tenants-subscription-summary"
          >
            {formatSubscriptionSummary(subscription)}
          </p>
        ) : subscriptionError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-subscription-error"
          >
            Subscription read failed
            {getApiErrorDetail(subscriptionErr)
              ? `: ${getApiErrorDetail(subscriptionErr)}`
              : "."}
          </p>
        ) : (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-subscription-empty"
          >
            No subscription row for this tenant (GET 404).
          </p>
        )}
      </div>

      {billingUnavailableDetail ? (
        <div
          className="rounded-md border border-warning-300 bg-warning-50 p-3 text-sm text-warning-800 dark:border-warning-700 dark:bg-warning-950/40 dark:text-warning-200"
          data-testid="admin-tenants-billing-unavailable"
        >
          <p className="font-medium">Billing unavailable</p>
          <p className="mt-1">{billingUnavailableDetail}</p>
          <p className="mt-1 text-xs">
            Set real <code>STRIPE_SECRET_KEY</code> in ops env. Do not invent
            keys in the UI.
          </p>
        </div>
      ) : null}

      <div className="space-y-2" data-testid="admin-tenants-billing-catalog">
        <p className="text-sm font-medium text-[var(--text-secondary)]">
          Catalog plan
        </p>
        {catalogLoading ? (
          <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <Spinner className="h-4 w-4" /> Loading catalog…
          </div>
        ) : catalogError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-catalog-error"
          >
            Catalog unavailable
            {getApiErrorDetail(catalogErr)
              ? `: ${getApiErrorDetail(catalogErr)}`
              : "."}
          </p>
        ) : !catalog || catalog.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-catalog-empty"
          >
            No active plans in billing catalog. Bind real Stripe Price ids on
            plans via Owner plan admin (ops).
          </p>
        ) : (
          <>
            <div data-testid="admin-tenants-catalog-plan">
              <Select
                value={selectedPlanId}
                onChange={setSelectedPlanId}
                options={[
                  { label: "Select plan…", value: "" },
                  ...planOptions,
                ]}
                placeholder="Select plan…"
              />
            </div>
            <div data-testid="admin-tenants-billing-cycle">
              <Select
                value={billingCycle}
                onChange={(v) =>
                  setBillingCycle(v === "yearly" ? "yearly" : "monthly")
                }
                options={[
                  { label: "Monthly", value: "monthly" },
                  { label: "Yearly", value: "yearly" },
                ]}
                placeholder="Billing cycle"
              />
            </div>
            <p
              className="text-xs text-[var(--text-muted)]"
              data-testid="admin-tenants-catalog-price"
            >
              {selectedPlan
                ? resolvedCatalogPrice
                  ? `Resolved price_id=${resolvedCatalogPrice}`
                  : `No stripe_price_id_${billingCycle} on this plan`
                : "Select a plan to resolve Stripe Price id from catalog"}
            </p>
          </>
        )}
      </div>

      <div className="space-y-2">
        <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
          Optional override <code>price_id</code> (real Stripe id from ops)
        </label>
        <Input
          value={manualPriceId}
          onChange={(e) => setManualPriceId(e.target.value)}
          placeholder="price_… (optional override)"
          data-testid="admin-tenants-checkout-price-id"
        />
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCheckout}
            disabled={checkoutMutation.isPending}
            data-testid="admin-tenants-checkout-create"
          >
            {checkoutMutation.isPending
              ? "Creating Checkout…"
              : "Create Checkout Session"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handlePortal}
            disabled={portalMutation.isPending}
            data-testid="admin-tenants-portal-open"
          >
            {portalMutation.isPending
              ? "Opening Portal…"
              : "Open Customer Portal"}
          </Button>
        </div>
      </div>

      <div data-testid="admin-tenants-platform-invoices">
        <p className="mb-1 text-sm font-medium text-[var(--text-secondary)]">
          Platform invoices
        </p>
        {invoicesLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading invoices…</p>
        ) : invoicesError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-invoices-error"
          >
            Invoices unavailable
            {getApiErrorDetail(invoicesErr)
              ? `: ${getApiErrorDetail(invoicesErr)}`
              : "."}
          </p>
        ) : !invoices || invoices.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-invoices-empty"
          >
            No platform invoices for this tenant yet (webhook sync after Stripe
            invoices).
          </p>
        ) : (
          <ul
            className="max-h-40 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-tenants-invoices-list"
          >
            {invoices.map((inv) => (
              <li
                key={inv.id}
                className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-default)] py-1"
              >
                <span>
                  {inv.status} · {inv.amount} {inv.currency} ·{" "}
                  {inv.stripe_invoice_id}
                </span>
                {inv.hosted_invoice_url ? (
                  <a
                    href={inv.hosted_invoice_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[var(--muhide-orange)] underline"
                  >
                    Open
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div
        className="space-y-2 border-t border-[var(--border-default)] pt-3"
        data-testid="admin-tenants-usage-meters"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-medium text-[var(--text-secondary)]">
            Usage meters (hourly rollup)
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRollup}
            disabled={rollupMutation.isPending}
            data-testid="admin-tenants-usage-rollup"
          >
            {rollupMutation.isPending ? "Rolling up…" : "Run rollup"}
          </Button>
        </div>
        <div data-testid="admin-tenants-usage-metric-filter">
          <Select
            value={metricFilter}
            onChange={setMetricFilter}
            options={[...ADMIN_USAGE_METRIC_OPTIONS]}
            placeholder="Metric filter"
          />
        </div>
        {usageLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading usage…</p>
        ) : usageError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-usage-error"
          >
            Usage meters unavailable
            {getApiErrorDetail(usageErr)
              ? `: ${getApiErrorDetail(usageErr)}`
              : "."}
          </p>
        ) : !usageMeters || usageMeters.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-usage-empty"
          >
            No rolled-up usage meters yet. Record events via API then Run
            rollup (STORY-05-03). Not Production GO.
          </p>
        ) : (
          <ul
            className="max-h-40 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-tenants-usage-list"
          >
            {usageMeters.map((m) => (
              <li
                key={m.id}
                className="border-b border-[var(--border-default)] py-1 font-mono"
              >
                {formatUsageMeterRow(m)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
