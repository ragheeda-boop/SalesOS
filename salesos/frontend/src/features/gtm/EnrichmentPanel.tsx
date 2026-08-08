"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useEnrichmentDetail,
  useEnrichmentList,
  useEnrichmentMeta,
  useRunEnrichment,
} from "@/lib/hooks/enrichmentQueries";
import type { EnrichmentRun } from "@/lib/api";
import { ENRICHMENT_HONESTY, ENRICHMENT_NON_GOALS } from "@/features/gtm/enrichmentHonesty";
import {
  buildIcpProfileHref,
  buildLeadDiscoveryHref,
  buildVerificationHref,
  contactFieldsFromFilled,
} from "@/features/gtm/gtmHandoff";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S11-05 — Enrichment Waterfall against tip STORY-11-05 HTTP.
 * ≥2 FakeEnrichment providers. Not Production GO / RAG GO.
 */
export function EnrichmentPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useEnrichmentMeta();
  const listQuery = useEnrichmentList();
  const runMutation = useRunEnrichment();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useEnrichmentDetail(selectedId);

  const [companyName, setCompanyName] = useState("Acme Pilot Co");
  const [domain, setDomain] = useState("acme.example");
  const [externalId, setExternalId] = useState("");
  const [knownIndustry, setKnownIndustry] = useState("");
  const [knownCity, setKnownCity] = useState("");
  const [providerOrder, setProviderOrder] = useState("");
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const run = searchParams.get("run");
    if (run) setSelectedId(run);
    const name = searchParams.get("company_name");
    if (name?.trim()) setCompanyName(name.trim());
    const d = searchParams.get("domain");
    if (d?.trim()) setDomain(d.trim());
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadRun(row: EnrichmentRun) {
    setSelectedId(row.id);
    setCompanyName(row.request.company_name);
    setDomain(row.request.domain ?? "");
    setExternalId(row.request.external_id ?? "");
    const known = row.request.known ?? {};
    setKnownIndustry(known.industry == null ? "" : String(known.industry));
    setKnownCity(known.city == null ? "" : String(known.city));
    setProviderOrder((row.request.provider_order ?? []).join(", "));
  }

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="enrichment-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="enrichment-honesty"
      >
        {ENRICHMENT_HONESTY} Non-goals: {ENRICHMENT_NON_GOALS.join("; ")}. Not Production GO / RAG
        GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="enrichment-meta"
        >
          <p>
            providers {(metaQuery.data.providers_configured ?? []).join(", ") || "—"} · fields{" "}
            {(metaQuery.data.enrichable_fields ?? []).join(", ")}
          </p>
          <p data-testid="enrichment-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
          <p>{metaQuery.data.policy}</p>
        </div>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : (
        <Spinner />
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          data-testid="enrichment-refresh"
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <span className="text-xs text-[var(--text-muted)]" data-testid="enrichment-count">
          {listQuery.data?.length ?? 0} run(s)
        </span>
      </div>

      <ul
        className="max-h-48 space-y-1 overflow-y-auto rounded border border-[var(--border-default)] p-2"
        data-testid="enrichment-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="text-xs text-[var(--text-muted)]">
            No enrichment runs yet. Submit a seed below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li key={row.id}>
              <button
                type="button"
                className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-[var(--bg-muted)] ${
                  selectedId === row.id ? "bg-[var(--bg-muted)] font-medium" : ""
                }`}
                data-testid="enrichment-row"
                onClick={() => loadRun(row)}
              >
                {row.request.company_name} ·{" "}
                {row.complete ? "complete" : `missing ${row.missing_fields.length}`} ·{" "}
                {row.providers_attempted.join("→") || "—"}
              </button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="enrichment-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!companyName.trim()) {
            toast({
              title: "Company required",
              description: "Provide a company_name seed.",
              variant: "error",
            });
            return;
          }
          const known: Record<string, unknown> = {};
          if (knownIndustry.trim()) known.industry = knownIndustry.trim();
          if (knownCity.trim()) known.city = knownCity.trim();
          const order = providerOrder
            .split(/[,;\n]/)
            .map((s) => s.trim())
            .filter(Boolean);
          runMutation.mutate(
            {
              company_name: companyName.trim(),
              domain: domain.trim() || undefined,
              external_id: externalId.trim() || undefined,
              known: Object.keys(known).length ? known : undefined,
              provider_order: order.length ? order : undefined,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  title: "Enrichment run complete",
                  description: `${Object.keys(row.filled).length} field(s) filled · ${
                    row.complete ? "complete" : "partial"
                  }`,
                });
              },
              onError: (err) => {
                toast({
                  title: "Enrichment failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Run enrichment waterfall (tip POST)
        </h2>
        <Input
          label="Company name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          data-testid="enrichment-company"
        />
        <Input
          label="Domain"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          data-testid="enrichment-domain"
        />
        <Input
          label="External id"
          value={externalId}
          onChange={(e) => setExternalId(e.target.value)}
          data-testid="enrichment-external-id"
        />
        <Input
          label="Known industry (lock)"
          value={knownIndustry}
          onChange={(e) => setKnownIndustry(e.target.value)}
          data-testid="enrichment-known-industry"
        />
        <Input
          label="Known city (lock)"
          value={knownCity}
          onChange={(e) => setKnownCity(e.target.value)}
          data-testid="enrichment-known-city"
        />
        <Input
          label="Provider order (csv, optional)"
          value={providerOrder}
          onChange={(e) => setProviderOrder(e.target.value)}
          placeholder="fake_b, fake_a"
          data-testid="enrichment-provider-order"
        />
        <Button type="submit" disabled={runMutation.isPending} data-testid="enrichment-run">
          {runMutation.isPending ? "Running…" : "Enrich"}
        </Button>
      </form>

      {selectedId ? (
        <div
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="enrichment-detail"
        >
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">{getApiError(detailQuery.error)}</p>
          ) : active ? (
            <>
              <p className="font-mono text-xs text-[var(--text-muted)]">
                run {active.id} · complete={String(active.complete)} · attempted{" "}
                {active.providers_attempted.join("→")}
              </p>
              <div data-testid="enrichment-filled">
                <h3 className="text-sm font-semibold">Filled</h3>
                <pre className="mt-1 overflow-x-auto rounded bg-[var(--bg-muted)] p-2 text-xs">
                  {JSON.stringify(active.filled, null, 2)}
                </pre>
              </div>
              <div data-testid="enrichment-hits">
                <h3 className="text-sm font-semibold">Hits</h3>
                <ul className="mt-1 space-y-1 text-xs">
                  {active.hits.map((h, i) => (
                    <li key={`${h.field}-${i}`}>
                      {h.field}={String(h.value)} ← {h.provider_key}
                    </li>
                  ))}
                </ul>
              </div>
              {active.missing_fields.length > 0 ? (
                <p className="text-xs text-[var(--text-muted)]" data-testid="enrichment-missing">
                  Missing: {active.missing_fields.join(", ")}
                </p>
              ) : null}
              {(() => {
                const contact = contactFieldsFromFilled(active.filled);
                if (!contact.email && !contact.phone) return null;
                return (
                  <Link
                    href={buildVerificationHref(contact)}
                    className="inline-flex text-sm underline text-[var(--text-primary)]"
                    data-testid="enrichment-handoff-verification"
                  >
                    Verify filled email/phone →
                  </Link>
                );
              })()}
              <Link
                href={buildLeadDiscoveryHref({
                  name: `${active.request.company_name} discovery`,
                  industries: active.filled.industry == null ? "" : String(active.filled.industry),
                  cities: active.filled.city == null ? "" : String(active.filled.city),
                  employees_min: "",
                  employees_max: "",
                })}
                className="block text-sm underline text-[var(--text-primary)]"
                data-testid="enrichment-handoff-lead-discovery"
              >
                Open Lead Discovery with filled industry/city →
              </Link>
            </>
          ) : null}
        </div>
      ) : null}

      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href={buildIcpProfileHref()} className="underline">
          /gtm/icp
        </Link>
        {" · "}
        <Link href="/gtm/lead-discovery" className="underline">
          /gtm/lead-discovery
        </Link>
        {" · "}
        <Link href={buildVerificationHref()} className="underline">
          /gtm/verification
        </Link>
        .
      </p>
    </div>
  );
}
