"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useMarketplaceListing,
  useMarketplaceListings,
  useMarketplaceListingsMeta,
  useSeedFirstPartyMarketplaceListings,
} from "@/lib/hooks/marketplaceListingsQueries";
import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "@/features/marketplace-listings/marketplaceListingsHonesty";
import type { MarketplaceListing } from "@/lib/api";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S13-01b — Marketplace listings browse (tip STORY-13-01 read-only).
 * No install/certify UI. Not CAP-036 stub. Not Production GO.
 */
export function MarketplaceListingsBrowse() {
  const { toast } = useToast();
  const [listingType, setListingType] = useState("");
  const [status, setStatus] = useState("");
  const [detailKey, setDetailKey] = useState<string | null>(null);

  const metaQuery = useMarketplaceListingsMeta();
  const listQuery = useMarketplaceListings({
    listing_type: listingType.trim() || undefined,
    status: status.trim() || undefined,
  });
  const detailQuery = useMarketplaceListing(detailKey);
  const seedMutation = useSeedFirstPartyMarketplaceListings();

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
          {seedMutation.isPending ? "Seeding…" : "Seed first-party (Odoo/HubSpot)"}
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
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      data-testid="marketplace-listings-open-detail"
                      onClick={() => setDetailKey(row.slug || row.id)}
                    >
                      Detail
                    </Button>
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
            <pre
              className="overflow-x-auto rounded bg-[var(--bg-muted)] p-2 font-mono text-xs"
              data-testid="marketplace-listings-detail-result"
            >
              {JSON.stringify(detailQuery.data, null, 2)}
            </pre>
          ) : null}
          <p className="text-xs text-[var(--text-muted)]">
            Install / certify UI is STANDBY until STORY-13-02 transitions.
          </p>
        </section>
      ) : null}
    </div>
  );
}
