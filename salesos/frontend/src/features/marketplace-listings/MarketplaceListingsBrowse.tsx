"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCertifyMarketplaceListing,
  useInstallMarketplaceListing,
  useMarketplaceCatalogInstalls,
  useMarketplaceCertifyMeta,
  useMarketplaceListing,
  useMarketplaceListings,
  useMarketplaceListingsMeta,
  usePublishMarketplaceListing,
  useSeedFirstPartyMarketplaceListings,
  useSeedMarketplacePublishPack,
  useSubmitMarketplaceListing,
} from "@/lib/hooks/marketplaceListingsQueries";
import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "@/features/marketplace-listings/marketplaceListingsHonesty";
import type {
  MarketplaceCatalogInstall,
  MarketplaceCertifyReport,
  MarketplaceListing,
} from "@/lib/api";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S13-04 — Marketplace listings browse + certify + publish/install.
 * Catalog install ≠ live ERP. Not CAP-036 stub. Not Production GO.
 */
export function MarketplaceListingsBrowse() {
  const { toast } = useToast();
  const [listingType, setListingType] = useState("");
  const [status, setStatus] = useState("");
  const [detailKey, setDetailKey] = useState<string | null>(null);
  const [lastCertify, setLastCertify] = useState<MarketplaceCertifyReport | null>(null);
  const [lastInstall, setLastInstall] = useState<MarketplaceCatalogInstall | null>(null);

  const metaQuery = useMarketplaceListingsMeta();
  const certifyMetaQuery = useMarketplaceCertifyMeta();
  const installsQuery = useMarketplaceCatalogInstalls();
  const listQuery = useMarketplaceListings({
    listing_type: listingType.trim() || undefined,
    status: status.trim() || undefined,
  });
  const detailQuery = useMarketplaceListing(detailKey);
  const seedMutation = useSeedFirstPartyMarketplaceListings();
  const seedPackMutation = useSeedMarketplacePublishPack();
  const submitMutation = useSubmitMarketplaceListing();
  const certifyMutation = useCertifyMarketplaceListing();
  const publishMutation = usePublishMarketplaceListing();
  const installMutation = useInstallMarketplaceListing();

  const actionId = detailQuery.data?.id || detailQuery.data?.slug || detailKey || "";

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
      }
    );
  }

  function runPublish(id: string) {
    publishMutation.mutate(id, {
      onSuccess: (row: MarketplaceListing) => {
        toast({
          title: "Published",
          description: `${row.slug} → ${row.status} · installable=${String(row.installable)}`,
        });
      },
      onError: (err: unknown) => {
        toast({
          title: "Publish failed",
          description: getApiError(err),
          variant: "error",
        });
      },
    });
  }

  function runInstall(id: string) {
    installMutation.mutate(id, {
      onSuccess: (rec: MarketplaceCatalogInstall) => {
        setLastInstall(rec);
        toast({
          title: "Catalog install recorded",
          description: `${rec.listing_slug} (not live ERP)`,
        });
      },
      onError: (err: unknown) => {
        toast({
          title: "Install failed",
          description: getApiError(err),
          variant: "error",
        });
      },
    });
  }

  const busy =
    submitMutation.isPending ||
    certifyMutation.isPending ||
    publishMutation.isPending ||
    installMutation.isPending;

  return (
    <div className="space-y-4" data-testid="marketplace-listings-browse">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="marketplace-listings-honesty"
      >
        {MARKETPLACE_LISTINGS_HONESTY} Non-goals: {MARKETPLACE_LISTINGS_NON_GOALS.join("; ")}.
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
            void installsQuery.refetch();
            void listQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <Button
          type="button"
          size="sm"
          data-testid="marketplace-listings-seed-pack"
          disabled={seedPackMutation.isPending}
          onClick={() => {
            seedPackMutation.mutate(undefined, {
              onSuccess: (rows: MarketplaceListing[]) => {
                toast({
                  title: "Seeded publish pack",
                  description: `${rows.length} listing(s) (idempotent)`,
                });
              },
              onError: (err: unknown) => {
                toast({
                  title: "Seed publish pack failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            });
          }}
        >
          {seedPackMutation.isPending ? "Seeding…" : "Seed publish pack (13-04)"}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          data-testid="marketplace-listings-seed"
          disabled={seedMutation.isPending}
          onClick={() => {
            seedMutation.mutate(undefined, {
              onSuccess: (rows: MarketplaceListing[]) => {
                toast({
                  title: "Seeded (seed-first-party alias)",
                  description: `${rows.length} listing(s)`,
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
          {seedMutation.isPending ? "Seeding…" : "Seed first-party (alias)"}
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
          <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
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
        <h2 className="text-sm font-semibold">Certify meta (tip GET /certify/meta)</h2>
        {certifyMetaQuery.isLoading ? (
          <Spinner />
        ) : certifyMetaQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(certifyMetaQuery.error)}</p>
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
            <p>{certifyMetaQuery.data.honesty}</p>
          </div>
        ) : null}
      </section>

      <section
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="marketplace-listings-list"
      >
        <h2 className="text-sm font-semibold">Catalog (tip GET /marketplace/listings)</h2>
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
          <p className="text-sm text-[var(--text-danger)]">{getApiError(listQuery.error)}</p>
        ) : listQuery.data ? (
          listQuery.data.length === 0 ? (
            <p
              className="text-sm text-[var(--text-muted)]"
              data-testid="marketplace-listings-empty"
            >
              No listings in memory catalog. Use Seed publish pack (13-04).
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
                        {row.slug} · {row.listing_type} · {row.version} · {row.status}
                        {row.installable ? " · installable" : ""}
                      </span>
                      {row.description ? (
                        <p className="text-xs text-[var(--text-muted)]">{row.description}</p>
                      ) : null}
                      <p className="text-xs text-[var(--text-muted)]">
                        {row.publisher}
                        {row.first_party ? " · first-party" : ""}
                        {row.connector_key ? ` · connector_key=${row.connector_key}` : ""}
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
                        variant="secondary"
                        data-testid="marketplace-listings-row-certify"
                        disabled={busy}
                        onClick={() => runCertify(row.id, true)}
                      >
                        Certify
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        data-testid="marketplace-listings-row-publish"
                        disabled={busy}
                        onClick={() => runPublish(row.id)}
                      >
                        Publish
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        data-testid="marketplace-listings-row-install"
                        disabled={busy || row.installable === false}
                        onClick={() => runInstall(row.id)}
                      >
                        Install
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )
        ) : null}
      </section>

      <section
        className="space-y-2 rounded border border-[var(--border-default)] p-4"
        data-testid="marketplace-listings-installs"
      >
        <h2 className="text-sm font-semibold">Catalog installs (tip GET /installs)</h2>
        <p className="text-xs text-[var(--text-muted)]">
          Memory receipts only — not live HubSpot/Odoo/REST GO.
        </p>
        {installsQuery.isLoading ? (
          <Spinner />
        ) : installsQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">{getApiError(installsQuery.error)}</p>
        ) : installsQuery.data ? (
          installsQuery.data.length === 0 ? (
            <p
              className="text-sm text-[var(--text-muted)]"
              data-testid="marketplace-listings-installs-empty"
            >
              No catalog installs for this tenant yet.
            </p>
          ) : (
            <ul className="space-y-1 font-mono text-xs">
              {installsQuery.data.map((rec: MarketplaceCatalogInstall) => (
                <li key={rec.id} data-testid="marketplace-listings-install-row">
                  {rec.listing_slug} · {rec.listing_type}
                  {rec.connector_key ? ` · ${rec.connector_key}` : ""} · {rec.installed_at}
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
            <h2 className="text-sm font-semibold">Detail (tip GET /{"{id|slug}"})</h2>
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
            <p className="text-sm text-[var(--text-danger)]">{getApiError(detailQuery.error)}</p>
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
                  Submit
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="marketplace-listings-detail-certify"
                  disabled={busy || !actionId}
                  onClick={() => runCertify(actionId, true)}
                >
                  Certify
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  data-testid="marketplace-listings-detail-publish"
                  disabled={busy || !actionId}
                  onClick={() => runPublish(actionId)}
                >
                  {publishMutation.isPending ? "Publishing…" : "Publish"}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  data-testid="marketplace-listings-detail-install"
                  disabled={busy || !actionId || detailQuery.data.installable === false}
                  onClick={() => runInstall(actionId)}
                >
                  {installMutation.isPending ? "Installing…" : "Catalog install"}
                </Button>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Catalog install writes a tenant-scoped memory receipt. It does not enable live
                ERP/CRM sync.
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

      {lastInstall ? (
        <section
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="marketplace-listings-install-report"
        >
          <h2 className="text-sm font-semibold">Last catalog install</h2>
          <pre
            className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
            data-testid="marketplace-listings-install-report-result"
          >
            {JSON.stringify(lastInstall, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
