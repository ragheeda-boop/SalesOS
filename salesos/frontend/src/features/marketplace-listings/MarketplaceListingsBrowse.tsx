"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCertifyMarketplaceListing,
  useMarketplaceCertifyMeta,
  useMarketplaceListing,
  useMarketplaceListings,
  useMarketplaceListingsMeta,
  useSeedFirstPartyMarketplaceListings,
  useSubmitMarketplaceListing,
} from "@/lib/hooks/marketplaceListingsQueries";
import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "@/features/marketplace-listings/marketplaceListingsHonesty";
import type { MarketplaceCertifyReport, MarketplaceListing } from "@/lib/api";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S13-03 — Marketplace listings browse + tip certify (STORY-13-01/02).
 * No invented install HTTP. Not CAP-036 stub. Not Production GO.
 */
export function MarketplaceListingsBrowse() {
  const { toast } = useToast();
  const [listingType, setListingType] = useState("");
  const [status, setStatus] = useState("");
  const [detailKey, setDetailKey] = useState<string | null>(null);
  const [lastCertify, setLastCertify] =
    useState<MarketplaceCertifyReport | null>(null);

  const metaQuery = useMarketplaceListingsMeta();
  const certifyMetaQuery = useMarketplaceCertifyMeta();
  const listQuery = useMarketplaceListings({
    listing_type: listingType.trim() || undefined,
    status: status.trim() || undefined,
  });
  const detailQuery = useMarketplaceListing(detailKey);
  const seedMutation = useSeedFirstPartyMarketplaceListings();
  const submitMutation = useSubmitMarketplaceListing();
  const certifyMutation = useCertifyMarketplaceListing();

  const actionId =
    detailQuery.data?.id || detailQuery.data?.slug || detailKey || "";

  function runSubmit(id: string) {
    submitMutation.mutate(id, {
      onSuccess: (row: MarketplaceListing) => {
        toast({
          title: "Submitted for certification",
          description: `${row.slug} → ${row.status}`,
        });
      },
      onError: (err: unknown) => {
        toast({
          title: "Submit failed",
          description: getApiError(err),
          variant: "error",
        });
      },
    });
  }

  function runCertify(id: string, autoSubmit: boolean) {
    certifyMutation.mutate(
      { listingIdOrSlug: id, body: { auto_submit: autoSubmit } },
      {
        onSuccess: (report: MarketplaceCertifyReport) => {
          setLastCertify(report);
          toast({
            title: report.ok ? "Certified" : "Certify returned",
            description: `${report.listing_id}: ${report.status_before} → ${report.status_after}`,
            variant: report.ok ? "success" : "error",
          });
        },
        onError: (err: unknown) => {
          toast({
            title: "Certify failed",
            description: getApiError(err),
            variant: "error",
          });
        },
      },
    );
  }

  const busy = submitMutation.isPending || certifyMutation.isPending;

  return (
    <div className="space-y-4" data-testid="marketplace-listings-browse">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="marketplace-listings-honesty"
      >
        {MARKETPLACE_LISTINGS_HONESTY} Non-goals:{" "}
        {MARKETPLACE_LISTINGS_NON_GOALS.join("; ")}.
      </p>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="secondary"
          data-testid="marketplace-listings-refresh"
          onClick={() => {
            void metaQuery.refetch();
            void certifyMetaQuery.refetch();
            void listQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <Button
          type="button"
          size="sm"
          data-testid="marketplace-listings-seed"
          disabled={seedMutation.isPending}
          onClick={() => {
            seedMutation.mutate(undefined, {
              onSuccess: (rows: MarketplaceListing[]) => {
                toast({
                  title: "Seeded first-party connectors",
                  description: `${rows.length} listing(s) (idempotent)`,
                });
              },
              onError: (err: unknown) => {
                toast({
                  title: "Seed failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            });
          }}
        >
          {seedMutation.isPending
            ? "Seeding…"
            : "Seed first-party (Odoo/HubSpot)"}
        </Button>
      </div>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="marketplace-listings-meta"
      >
        <h2 className="text-sm font-semibold">Meta (tip GET /meta)</h2>
        {metaQuery.isLoading ? (
          <Spinner />
        ) : metaQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(metaQuery.error)}
          </p>
        ) : metaQuery.data ? (
          <pre
            className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
            data-testid="marketplace-listings-meta-result"
          >
            {JSON.stringify(metaQuery.data, null, 2)}
          </pre>
        ) : null}
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="marketplace-listings-certify-meta"
      >
        <h2 className="text-sm font-semibold">
          Certify meta (tip GET /certify/meta)
        </h2>
        {certifyMetaQuery.isLoading ? (
          <Spinner />
        ) : certifyMetaQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(certifyMetaQuery.error)}
          </p>
        ) : certifyMetaQuery.data ? (
          <div
            className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
            data-testid="marketplace-listings-certify-meta-result"
          >
            <p>
              {certifyMetaQuery.data.capability} · stages=
              {certifyMetaQuery.data.stages.join(", ")} · suite=
              {certifyMetaQuery.data.conformance_suite}
            </p>
            <p>via={certifyMetaQuery.data.via}</p>
            <p>sandbox={certifyMetaQuery.data.trial_sandbox}</p>
            <p>
              feature_ai_copilot=
              {String(certifyMetaQuery.data.feature_ai_copilot)}
            </p>
            <p>{certifyMetaQuery.data.honesty}</p>
          </div>
        ) : null}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="marketplace-listings-list"
      >
        <h2 className="text-sm font-semibold">
          Catalog (tip GET /marketplace/listings)
        </h2>
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="listing_type (optional)"
            value={listingType}
            onChange={(e) => setListingType(e.target.value)}
            className="max-w-xs"
            data-testid="marketplace-listings-type-filter"
            placeholder="connector | app | prompt_pack | playbook"
          />
          <Input
            label="status (optional)"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="max-w-xs"
            data-testid="marketplace-listings-status-filter"
            placeholder="draft | published | …"
          />
        </div>
        {listQuery.isLoading ? (
          <Spinner />
        ) : listQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(listQuery.error)}
          </p>
        ) : listQuery.data ? (
          listQuery.data.length === 0 ? (
            <p
              className="text-sm text-[var(--text-muted)]"
              data-testid="marketplace-listings-empty"
            >
              No listings in memory catalog. Use Seed first-party or wait for
              Owner upserts. Persistence is memory (process-local).
            </p>
          ) : (
            <ul className="space-y-2 text-sm">
              {listQuery.data.map((row: MarketplaceListing) => (
                <li
                  key={row.id}
                  className="rounded border border-[var(--border-default)] px-3 py-2"
                  data-testid="marketplace-listings-row"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <span className="font-medium">{row.name}</span>{" "}
                      <span className="font-mono text-xs text-[var(--text-muted)]">
                        {row.slug} · {row.listing_type} · {row.version} ·{" "}
                        {row.status}
                      </span>
                      {row.description ? (
                        <p className="text-xs text-[var(--text-muted)]">
                          {row.description}
                        </p>
                      ) : null}
                      <p className="text-xs text-[var(--text-muted)]">
                        {row.publisher}
                        {row.first_party ? " · first-party" : ""}
                        {row.connector_key
                          ? ` · connector_key=${row.connector_key}`
                          : ""}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        data-testid="marketplace-listings-open-detail"
                        onClick={() => setDetailKey(row.slug || row.id)}
                      >
                        Detail
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        data-testid="marketplace-listings-row-submit"
                        disabled={busy}
                        onClick={() => runSubmit(row.id)}
                      >
                        Submit
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        data-testid="marketplace-listings-row-certify"
                        disabled={busy}
                        onClick={() => runCertify(row.id, true)}
                      >
                        Certify
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )
        ) : null}
      </section>

      {detailKey ? (
        <section
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="marketplace-listings-detail"
        >
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">
              Detail (tip GET /{"{id|slug}"})
            </h2>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              data-testid="marketplace-listings-close-detail"
              onClick={() => setDetailKey(null)}
            >
              Close
            </Button>
          </div>
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">
              {getApiError(detailQuery.error)}
            </p>
          ) : detailQuery.data ? (
            <>
              <pre
                className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
                data-testid="marketplace-listings-detail-result"
              >
                {JSON.stringify(detailQuery.data, null, 2)}
              </pre>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="marketplace-listings-detail-submit"
                  disabled={busy || !actionId}
                  onClick={() => runSubmit(actionId)}
                >
                  {submitMutation.isPending
                    ? "Submitting…"
                    : "Submit for certification"}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  data-testid="marketplace-listings-detail-certify"
                  disabled={busy || !actionId}
                  onClick={() => runCertify(actionId, true)}
                >
                  {certifyMutation.isPending
                    ? "Certifying…"
                    : "Run certify (auto_submit)"}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="marketplace-listings-detail-certify-no-auto"
                  disabled={busy || !actionId}
                  onClick={() => runCertify(actionId, false)}
                >
                  Certify (no auto_submit)
                </Button>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Tip certify stages: conformance → security_checklist →
                sandboxed_trial. Trial install is pipeline-internal only — no
                separate tenant install HTTP on tip.
              </p>
            </>
          ) : null}
        </section>
      ) : null}

      {lastCertify ? (
        <section
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="marketplace-listings-certify-report"
        >
          <h2 className="text-sm font-semibold">Last certify report</h2>
          <pre
            className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
            data-testid="marketplace-listings-certify-report-result"
          >
            {JSON.stringify(lastCertify, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
