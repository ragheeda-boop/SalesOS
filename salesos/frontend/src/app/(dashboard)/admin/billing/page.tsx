"use client";

import { useState } from "react";
import Link from "next/link";
import { Button, Select, Spinner, useToast } from "@salesos/ui";
import {
  useAdminDunningCases,
  useAdminPlatformInvoices,
  useAdminStripeStatus,
  useApplyPendingAdminPlanChanges,
  useEvaluateAdminDunning,
} from "@/lib/hooks/adminQueries";
import {
  ADMIN_DUNNING_STATUS_OPTIONS,
  formatDunningCaseRow,
  formatStripeStatusBanner,
  getApiErrorDetail,
  stripeStatusTone,
} from "@/features/admin/lib/formatProvisionToast";

/**
 * FE-S06-01 — Owner Console /admin/billing read view.
 * Dunning + platform invoices + apply-pending plan changes. Not Production GO.
 */
export default function AdminBillingPage() {
  const { toast } = useToast();
  const [dunningStatus, setDunningStatus] = useState("");
  const {
    data: dunningCases,
    isLoading: dunningLoading,
    isError: dunningError,
    error: dunningErr,
    refetch: refetchDunning,
  } = useAdminDunningCases({
    status: dunningStatus || undefined,
    limit: 100,
  });
  const {
    data: invoices,
    isLoading: invoicesLoading,
    isError: invoicesError,
    error: invoicesErr,
  } = useAdminPlatformInvoices();
  const evaluateMutation = useEvaluateAdminDunning();
  const applyPendingMutation = useApplyPendingAdminPlanChanges();
  const {
    data: stripeStatus,
    isLoading: stripeStatusLoading,
    isError: stripeStatusError,
    error: stripeStatusErr,
  } = useAdminStripeStatus();

  return (
    <div className="space-y-6 p-6" data-testid="admin-billing-page">
      <div
        className={
          stripeStatusTone(stripeStatus) === "blocked"
            ? "rounded border border-red-300 bg-red-50 p-3 text-xs text-red-900"
            : stripeStatusTone(stripeStatus) === "warn"
              ? "rounded border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900"
              : "rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3 text-xs"
        }
        data-testid="admin-billing-stripe-status"
      >
        <p className="mb-1 font-medium">Stripe readiness (STORY-05-02c)</p>
        {stripeStatusLoading ? (
          <p>Loading…</p>
        ) : stripeStatusError ? (
          <p>
            Status unavailable
            {getApiErrorDetail(stripeStatusErr)
              ? `: ${getApiErrorDetail(stripeStatusErr)}`
              : "."}{" "}
            No invented keys. Not Production GO.
          </p>
        ) : (
          <p>{formatStripeStatusBanner(stripeStatus)}</p>
        )}
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--text-primary)]">
            Owner billing
          </h1>
          <p className="text-sm text-[var(--text-muted)]">
            STORY-05-02b/04/05 — invoices, dunning, apply-pending plan changes.
            Not Production GO.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={applyPendingMutation.isPending}
            data-testid="admin-billing-plan-apply-pending"
            onClick={async () => {
              try {
                const result = await applyPendingMutation.mutateAsync({});
                toast({
                  variant: "success",
                  title: "Pending plans applied",
                  description: Object.entries(result)
                    .map(([k, v]) => `${k}=${String(v)}`)
                    .join(" · "),
                });
              } catch (err: unknown) {
                toast({
                  variant: "error",
                  title: "Apply-pending failed",
                  description: getApiErrorDetail(err) || "failed",
                });
              }
            }}
          >
            {applyPendingMutation.isPending
              ? "Applying…"
              : "Apply due pending plans"}
          </Button>
          <Link
            href="/admin/tenants"
            className="text-sm text-[var(--muhide-orange)] underline"
            data-testid="admin-billing-tenants-link"
          >
            Tenant Owner Console
          </Link>
        </div>
      </div>

      <section
        className="space-y-3 rounded-lg border border-[var(--border-default)] p-4"
        data-testid="admin-billing-dunning"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-medium text-[var(--text-primary)]">
            Dunning cases
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <div
              className="min-w-[10rem]"
              data-testid="admin-billing-dunning-status"
            >
              <Select
                value={dunningStatus}
                onChange={setDunningStatus}
                options={[...ADMIN_DUNNING_STATUS_OPTIONS]}
                placeholder="Status"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={evaluateMutation.isPending}
              data-testid="admin-billing-dunning-evaluate"
              onClick={async () => {
                try {
                  const result = await evaluateMutation.mutateAsync({});
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
              }}
            >
              {evaluateMutation.isPending ? "Evaluating…" : "Evaluate grace"}
            </Button>
          </div>
        </div>
        {dunningLoading ? (
          <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <Spinner className="h-4 w-4" /> Loading dunning…
          </div>
        ) : dunningError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-billing-dunning-error"
          >
            Dunning unavailable
            {getApiErrorDetail(dunningErr)
              ? `: ${getApiErrorDetail(dunningErr)}`
              : "."}
          </p>
        ) : !dunningCases || dunningCases.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-billing-dunning-empty"
          >
            No dunning cases
            {dunningStatus ? ` with status=${dunningStatus}` : ""}.
          </p>
        ) : (
          <ul
            className="max-h-72 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-billing-dunning-list"
          >
            {dunningCases.map((c) => (
              <li
                key={c.id}
                className="border-b border-[var(--border-default)] py-1 font-mono"
              >
                tenant={c.tenant_id} · {formatDunningCaseRow(c)}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="space-y-3 rounded-lg border border-[var(--border-default)] p-4"
        data-testid="admin-billing-invoices"
      >
        <h2 className="font-medium text-[var(--text-primary)]">
          Platform invoices
        </h2>
        {invoicesLoading ? (
          <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <Spinner className="h-4 w-4" /> Loading invoices…
          </div>
        ) : invoicesError ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-billing-invoices-error"
          >
            Invoices unavailable
            {getApiErrorDetail(invoicesErr)
              ? `: ${getApiErrorDetail(invoicesErr)}`
              : "."}
          </p>
        ) : !invoices || invoices.length === 0 ? (
          <p
            className="text-sm text-[var(--text-muted)]"
            data-testid="admin-billing-invoices-empty"
          >
            No platform invoices yet.
          </p>
        ) : (
          <ul
            className="max-h-72 space-y-1 overflow-y-auto text-xs text-[var(--text-secondary)]"
            data-testid="admin-billing-invoices-list"
          >
            {invoices.map((inv) => (
              <li
                key={inv.id}
                className="border-b border-[var(--border-default)] py-1 font-mono"
              >
                {inv.status} · {inv.amount} {inv.currency} · tenant=
                {inv.tenant_id} · {inv.stripe_invoice_id}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
