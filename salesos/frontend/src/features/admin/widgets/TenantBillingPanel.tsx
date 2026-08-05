"use client";

import { useCallback, useMemo, useState } from "react";
import { Button, Input, Select, Spinner, useToast } from "@salesos/ui";
import type { AdminPlanChangeQuote } from "@/lib/api/types/admin";
import {
  useAdminBillingCatalog,
  useAdminDunningCases,
  useAdminPlans,
  useAdminPlatformInvoices,
  useAdminStripeStatus,
  useAdminTenantSubscription,
  useAdminUsageMeters,
  useApplyAdminPlanChange,
  useApplyPendingAdminPlanChanges,
  useClearAdminDunning,
  useCreateAdminStripeCheckoutSession,
  useCreateAdminStripePortalSession,
  useEvaluateAdminDunning,
  useQuoteAdminPlanChange,
  useRollupAdminUsage,
} from "@/lib/hooks/adminQueries";
import {
  ADMIN_USAGE_METRIC_OPTIONS,
  catalogPriceIdForCycle,
  formatDunningCaseRow,
  formatPendingPlanHonesty,
  formatPlanChangeQuote,
  formatResolvedPlanEntitlementsHonesty,
  formatStripeStatusBanner,
  formatSubscriptionSummary,
  formatUsageMeterRow,
  getApiErrorDetail,
  isStripeBillingUnavailableError,
  listDisabledEntitlementDomains,
  stripeBillingUnavailableDescription,
  stripeStatusTone,
} from "@/features/admin/lib/formatProvisionToast";

type BillingCycle = "monthly" | "yearly";

/**
 * FE-S05-01..06 + FE-S06-03 — billing, UsageMeter, dunning, plan-change,
 * and resolved Plan.entitlements honesty from Owner plans list.
 * Honest 503 / pending-plan empty-states. No invented Stripe keys. Not Production GO.
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
  const { data: ownerPlans } = useAdminPlans();
  const {
    data: stripeStatus,
    isLoading: stripeStatusLoading,
    isError: stripeStatusError,
    error: stripeStatusErr,
  } = useAdminStripeStatus();
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
  const {
    data: dunningCases,
    isLoading: dunningLoading,
    isError: dunningError,
    error: dunningErr,
    refetch: refetchDunning,
  } = useAdminDunningCases({ tenant_id: tenantId, limit: 20 });
  const checkoutMutation = useCreateAdminStripeCheckoutSession();
  const portalMutation = useCreateAdminStripePortalSession();
  const rollupMutation = useRollupAdminUsage();
  const evaluateDunningMutation = useEvaluateAdminDunning();
  const clearDunningMutation = useClearAdminDunning();
  const quotePlanMutation = useQuoteAdminPlanChange();
  const applyPlanMutation = useApplyAdminPlanChange();
  const applyPendingPlanMutation = useApplyPendingAdminPlanChanges();

  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly");
  const [manualPriceId, setManualPriceId] = useState("");
  const [billingUnavailableDetail, setBillingUnavailableDetail] = useState<string | null>(null);
  const [planChangeTargetId, setPlanChangeTargetId] = useState("");
  const [downgradeImmediate, setDowngradeImmediate] = useState(false);
  const [planQuote, setPlanQuote] = useState<AdminPlanChangeQuote | null>(null);

  const planOptions = useMemo(
    () =>
      (catalog || []).map((p) => ({
        label: `${p.name} (${p.tier})`,
        value: p.id,
      })),
    [catalog]
  );

  const selectedPlan = useMemo(
    () => (catalog || []).find((p) => p.id === selectedPlanId) || null,
    [catalog, selectedPlanId]
  );

  const resolvedCatalogPrice = selectedPlan
    ? catalogPriceIdForCycle(selectedPlan, billingCycle)
    : null;

  const resolvedPlan = useMemo(() => {
    const planId = subscription?.plan_id;
    if (!planId || !ownerPlans?.length) return null;
    return ownerPlans.find((p) => p.id === planId) || null;
  }, [ownerPlans, subscription?.plan_id]);

  const resolvedEntitlementsHonesty = useMemo(() => {
    if (!subscription?.plan_id) return null;
    if (!resolvedPlan) {
      return (
        `Subscription plan_id=${subscription.plan_id} - Owner plans list has no match yet ` +
        `(catalog checkout prices do not include entitlements JSON). Not Production GO.`
      );
    }
    return formatResolvedPlanEntitlementsHonesty({
      planId: resolvedPlan.id,
      planName: resolvedPlan.name,
      tier: resolvedPlan.tier,
      entitlements: resolvedPlan.entitlements,
      pendingPlanId: subscription.pending_plan_id,
    });
  }, [resolvedPlan, subscription]);

  const disabledDomains = useMemo(
    () => listDisabledEntitlementDomains(resolvedPlan?.entitlements),
    [resolvedPlan]
  );

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
    [toast]
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
        ...(priceOverride ? { price_id: priceOverride } : { plan_id: selectedPlanId }),
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
        description: getApiErrorDetail(err) || "Stripe Checkout Session create failed",
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
        typeof (err as { response?: { status?: unknown } }).response?.status === "number"
          ? (err as { response: { status: number } }).response.status
          : null;
      toast({
        variant: "error",
        title: status === 409 ? "Portal needs Checkout first" : "Portal Session failed",
        description: getApiErrorDetail(err) || "Complete Checkout so stripe_customer_id exists",
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

  const handleEvaluateDunning = useCallback(async () => {
    try {
      const result = await evaluateDunningMutation.mutateAsync({});
      await refetchDunning();
      toast({
        variant: "success",
        title: "Dunning evaluate complete",
        description: Object.entries(result)
          .map(([k, v]) => `${k}=${String(v)}`)
          .join(" · "),
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Dunning evaluate failed",
        description: getApiErrorDetail(err) || "evaluate failed",
      });
    }
  }, [evaluateDunningMutation, refetchDunning, toast]);

  const handleClearDunning = useCallback(async () => {
    try {
      const result = await clearDunningMutation.mutateAsync(tenantId);
      await refetchDunning();
      toast({
        variant: "success",
        title: "Dunning cleared",
        description: `cleared=${result.cleared}`,
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Clear dunning failed",
        description: getApiErrorDetail(err) || "no open case or error",
      });
    }
  }, [clearDunningMutation, tenantId, refetchDunning, toast]);

  const handleQuotePlan = useCallback(async () => {
    if (!planChangeTargetId) {
      toast({
        variant: "error",
        title: "Select target plan",
        description: "Pick a catalog plan UUID for quote/apply.",
      });
      return;
    }
    try {
      const q = await quotePlanMutation.mutateAsync({
        tenant_id: tenantId,
        target_plan_id: planChangeTargetId,
        downgrade_immediate: downgradeImmediate,
      });
      setPlanQuote(q);
      toast({
        variant: "success",
        title: "Plan-change quote",
        description: formatPlanChangeQuote(q),
      });
    } catch (err: unknown) {
      setPlanQuote(null);
      toast({
        variant: "error",
        title: "Quote failed",
        description: getApiErrorDetail(err) || "plan-change quote failed",
      });
    }
  }, [planChangeTargetId, quotePlanMutation, tenantId, downgradeImmediate, toast]);

  const handleApplyPlan = useCallback(async () => {
    if (!planChangeTargetId) {
      toast({
        variant: "error",
        title: "Select target plan",
        description: "Quote first, then apply.",
      });
      return;
    }
    try {
      const q = await applyPlanMutation.mutateAsync({
        tenant_id: tenantId,
        target_plan_id: planChangeTargetId,
        downgrade_immediate: downgradeImmediate,
      });
      setPlanQuote(q);
      toast({
        variant: "success",
        title: "Plan-change applied",
        description: formatPlanChangeQuote(q),
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Apply failed",
        description: getApiErrorDetail(err) || "plan-change apply failed",
      });
    }
  }, [planChangeTargetId, applyPlanMutation, tenantId, downgradeImmediate, toast]);

  const handleApplyPendingPlans = useCallback(async () => {
    try {
      const result = await applyPendingPlanMutation.mutateAsync({});
      toast({
        variant: "success",
        title: "Pending plan changes applied",
        description: Object.entries(result)
          .map(([k, v]) => `${k}=${String(v)}`)
          .join(" · "),
      });
    } catch (err: unknown) {
      toast({
        variant: "error",
        title: "Apply-pending failed",
        description: getApiErrorDetail(err) || "apply-pending failed",
      });
    }
  }, [applyPendingPlanMutation, toast]);

  const openDunning = (dunningCases || []).filter((c) => c.status === "open");
  const pendingHonesty = subscription ? formatPendingPlanHonesty(subscription) : null;

  return (
    <div
      className="space-y-3 rounded-lg border border-[var(--border-default)] p-4"
      data-testid="admin-tenants-billing"
    >
      <div>
        <p className="font-medium text-[var(--text-primary)]">Billing / usage</p>
        <p className="text-xs text-[var(--text-muted)]">
          STORY-05-01..05 — catalog, Checkout, Portal, invoices, UsageMeter, dunning, plan-change.
          Fail-closed Stripe. Pending-plan honesty. Not Production GO.
        </p>
      </div>

      <div
        className={
          stripeStatusTone(stripeStatus) === "blocked"
            ? "rounded border border-[var(--status-danger-border)] bg-[var(--status-danger-bg)] p-3 text-xs text-[var(--status-danger-text)]"
            : stripeStatusTone(stripeStatus) === "warn"
              ? "rounded border border-[var(--status-warning-border)] bg-[var(--status-warning-bg)] p-3 text-xs text-[var(--status-warning-text)]"
              : "rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3 text-xs text-[var(--text-secondary)]"
        }
        data-testid="admin-tenants-stripe-status"
      >
        <p className="mb-1 font-medium">Stripe readiness (STORY-05-02c)</p>
        {stripeStatusLoading ? (
          <p>Loading stripe/status…</p>
        ) : stripeStatusError ? (
          <p data-testid="admin-tenants-stripe-status-error">
            Status unavailable
            {getApiErrorDetail(stripeStatusErr)
              ? `: ${getApiErrorDetail(stripeStatusErr)}`
              : "."}{" "}
            No invented keys.
          </p>
        ) : (
          <p data-testid="admin-tenants-stripe-status-summary">
            {formatStripeStatusBanner(stripeStatus)}
          </p>
        )}
      </div>

      <div data-testid="admin-tenants-subscription">
        {subscriptionLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading subscription…</p>
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
            {getApiErrorDetail(subscriptionErr) ? `: ${getApiErrorDetail(subscriptionErr)}` : "."}
          </p>
        ) : (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-subscription-empty"
          >
            No subscription row for this tenant (GET 404).
          </p>
        )}
        {pendingHonesty ? (
          <p
            className="mt-1 text-xs text-warning-700 dark:text-warning-400"
            data-testid="admin-tenants-pending-plan"
          >
            {pendingHonesty}
          </p>
        ) : null}
        {resolvedEntitlementsHonesty ? (
          <div
            className="mt-2 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] p-2 text-xs text-[var(--text-secondary)]"
            data-testid="admin-tenants-resolved-entitlements"
          >
            <p data-testid="admin-tenants-resolved-entitlements-summary">
              {resolvedEntitlementsHonesty}
            </p>
            {disabledDomains.length > 0 ? (
              <p
                className="mt-1 font-mono"
                data-testid="admin-tenants-resolved-entitlements-disabled"
              >
                Domains disabled (403 on gated paths): {disabledDomains.join(", ")}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>

      {billingUnavailableDetail ? (
        <div
          className="rounded-md border border-warning-300 bg-warning-50 p-3 text-sm text-warning-800 dark:border-warning-700 dark:bg-warning-950/40 dark:text-warning-200"
          data-testid="admin-tenants-billing-unavailable"
        >
          <p className="font-medium">Billing unavailable</p>
          <p className="mt-1">{billingUnavailableDetail}</p>
          <p className="mt-1 text-xs">
            Set real <code>STRIPE_SECRET_KEY</code> in ops env. Do not invent keys in the UI.
          </p>
        </div>
      ) : null}

      <div className="space-y-2" data-testid="admin-tenants-billing-catalog">
        <p className="text-sm font-medium text-[var(--text-secondary)]">Catalog plan</p>
        {catalogLoading ? (
          <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <Spinner className="h-4 w-4" /> Loading catalog…
          </div>
        ) : catalogError ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-catalog-error">
            Catalog unavailable
            {getApiErrorDetail(catalogErr) ? `: ${getApiErrorDetail(catalogErr)}` : "."}
          </p>
        ) : !catalog || catalog.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-catalog-empty">
            No active plans in billing catalog. Bind real Stripe Price ids on plans via Owner plan
            admin (ops).
          </p>
        ) : (
          <>
            <div data-testid="admin-tenants-catalog-plan">
              <Select
                value={selectedPlanId}
                onChange={setSelectedPlanId}
                options={[{ label: "Select plan…", value: "" }, ...planOptions]}
                placeholder="Select plan…"
              />
            </div>
            <div data-testid="admin-tenants-billing-cycle">
              <Select
                value={billingCycle}
                onChange={(v) => setBillingCycle(v === "yearly" ? "yearly" : "monthly")}
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
            {checkoutMutation.isPending ? "Creating Checkout…" : "Create Checkout Session"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handlePortal}
            disabled={portalMutation.isPending}
            data-testid="admin-tenants-portal-open"
          >
            {portalMutation.isPending ? "Opening Portal…" : "Open Customer Portal"}
          </Button>
        </div>
      </div>

      <div data-testid="admin-tenants-platform-invoices">
        <p className="mb-1 text-sm font-medium text-[var(--text-secondary)]">Platform invoices</p>
        {invoicesLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading invoices…</p>
        ) : invoicesError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-invoices-error"
          >
            Invoices unavailable
            {getApiErrorDetail(invoicesErr) ? `: ${getApiErrorDetail(invoicesErr)}` : "."}
          </p>
        ) : !invoices || invoices.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-tenants-invoices-empty"
          >
            No platform invoices for this tenant yet (webhook sync after Stripe invoices).
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
                  {inv.status} · {inv.amount} {inv.currency} · {inv.stripe_invoice_id}
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
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-usage-error">
            Usage meters unavailable
            {getApiErrorDetail(usageErr) ? `: ${getApiErrorDetail(usageErr)}` : "."}
          </p>
        ) : !usageMeters || usageMeters.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-usage-empty">
            No rolled-up usage meters yet. Record events via API then Run rollup (STORY-05-03). Not
            Production GO.
          </p>
        ) : (
          <ul
            className="max-h-40 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-tenants-usage-list"
          >
            {usageMeters.map((m) => (
              <li key={m.id} className="border-b border-[var(--border-default)] py-1 font-mono">
                {formatUsageMeterRow(m)}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div
        className="space-y-2 border-t border-[var(--border-default)] pt-3"
        data-testid="admin-tenants-plan-change"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-medium text-[var(--text-secondary)]">
            Plan change / proration (STORY-05-05)
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleApplyPendingPlans}
            disabled={applyPendingPlanMutation.isPending}
            data-testid="admin-tenants-plan-apply-pending"
          >
            {applyPendingPlanMutation.isPending ? "Applying pending…" : "Apply due pending"}
          </Button>
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          Upgrade = immediate prorated charge. Downgrade = period-end unless downgrade_immediate
          (credit now).
        </p>
        <div data-testid="admin-tenants-plan-change-target">
          <Select
            value={planChangeTargetId}
            onChange={setPlanChangeTargetId}
            options={[{ label: "Target plan…", value: "" }, ...planOptions]}
            placeholder="Target plan"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
          <input
            type="checkbox"
            checked={downgradeImmediate}
            onChange={(e) => setDowngradeImmediate(e.target.checked)}
            data-testid="admin-tenants-plan-downgrade-immediate"
          />
          Downgrade immediate (<code>downgrade_immediate=true</code>)
        </label>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleQuotePlan}
            disabled={quotePlanMutation.isPending}
            data-testid="admin-tenants-plan-quote"
          >
            {quotePlanMutation.isPending ? "Quoting…" : "Quote"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleApplyPlan}
            disabled={applyPlanMutation.isPending}
            data-testid="admin-tenants-plan-apply"
          >
            {applyPlanMutation.isPending ? "Applying…" : "Apply"}
          </Button>
        </div>
        {planQuote ? (
          <p
            className="text-xs font-mono text-[var(--text-secondary)]"
            data-testid="admin-tenants-plan-quote-summary"
          >
            {formatPlanChangeQuote(planQuote)}
          </p>
        ) : (
          <p
            className="text-xs text-[var(--text-muted)]"
            data-testid="admin-tenants-plan-quote-empty"
          >
            No quote yet — select target plan and Quote.
          </p>
        )}
      </div>

      <div
        className="space-y-2 border-t border-[var(--border-default)] pt-3"
        data-testid="admin-tenants-dunning"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-medium text-[var(--text-secondary)]">Dunning (STORY-05-04)</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleEvaluateDunning}
              disabled={evaluateDunningMutation.isPending}
              data-testid="admin-tenants-dunning-evaluate"
            >
              {evaluateDunningMutation.isPending ? "Evaluating…" : "Evaluate grace"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearDunning}
              disabled={clearDunningMutation.isPending || openDunning.length === 0}
              data-testid="admin-tenants-dunning-clear"
            >
              {clearDunningMutation.isPending ? "Clearing…" : "Clear open"}
            </Button>
          </div>
        </div>
        {dunningLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading dunning…</p>
        ) : dunningError ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-dunning-error">
            Dunning unavailable
            {getApiErrorDetail(dunningErr) ? `: ${getApiErrorDetail(dunningErr)}` : "."}
          </p>
        ) : !dunningCases || dunningCases.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]" data-testid="admin-tenants-dunning-empty">
            No dunning cases for this tenant.
          </p>
        ) : (
          <ul
            className="max-h-40 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-tenants-dunning-list"
          >
            {dunningCases.map((c) => (
              <li key={c.id} className="border-b border-[var(--border-default)] py-1 font-mono">
                {formatDunningCaseRow(c)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
