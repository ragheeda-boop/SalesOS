"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useLeadDiscoveryDetail,
  useLeadDiscoveryList,
  useLeadDiscoveryMeta,
  useRunLeadDiscovery,
} from "@/lib/hooks/leadDiscoveryQueries";
import type { LeadDiscoveryRun } from "@/lib/api";
import {
  LEAD_DISCOVERY_HONESTY,
  LEAD_DISCOVERY_NON_GOALS,
} from "@/features/gtm/leadDiscoveryHonesty";
import {
  buildEnrichmentHref,
  parseGtmCriteriaFromSearch,
} from "@/features/gtm/gtmHandoff";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

function splitCsv(raw: string): string[] {
  return raw
    .split(/[,;\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function parseOptionalInt(raw: string): number | null {
  const t = raw.trim();
  if (!t) return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return Math.trunc(n);
}

/**
 * FE-S11-03 / FE-S11-03b — Lead Discovery against tip STORY-11-03 HTTP.
 * Criteria handoff + ?run= deep-link. Not Production GO / RAG GO.
 */
export function LeadDiscoveryPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useLeadDiscoveryMeta();
  const listQuery = useLeadDiscoveryList();
  const runMutation = useRunLeadDiscovery();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useLeadDiscoveryDetail(selectedId);

  const [name, setName] = useState("Pilot discovery");
  const [industries, setIndustries] = useState("technology");
  const [cities, setCities] = useState("riyadh");
  const [employeesMin, setEmployeesMin] = useState("10");
  const [employeesMax, setEmployeesMax] = useState("500");
  const [limit, setLimit] = useState("25");
  const [useFallback, setUseFallback] = useState(true);
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const run = searchParams.get("run");
    if (run) setSelectedId(run);
    const handoff = parseGtmCriteriaFromSearch(searchParams);
    if (handoff.name?.trim()) setName(handoff.name.trim());
    if (handoff.industries.trim()) setIndustries(handoff.industries);
    if (handoff.cities.trim()) setCities(handoff.cities);
    if (handoff.employees_min.trim()) setEmployeesMin(handoff.employees_min);
    if (handoff.employees_max.trim()) setEmployeesMax(handoff.employees_max);
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadRun(row: LeadDiscoveryRun) {
    setSelectedId(row.id);
    setName(row.name);
    setIndustries((row.query.industries ?? []).join(", "));
    setCities((row.query.cities ?? []).join(", "));
    setEmployeesMin(
      row.query.employees_min == null ? "" : String(row.query.employees_min),
    );
    setEmployeesMax(
      row.query.employees_max == null ? "" : String(row.query.employees_max),
    );
    setLimit(String(row.query.limit ?? 25));
  }

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="lead-discovery-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="lead-discovery-honesty"
      >
        {LEAD_DISCOVERY_HONESTY} Non-goals:{" "}
        {LEAD_DISCOVERY_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="lead-discovery-meta"
        >
          <p>
            scale_hint {metaQuery.data.dataset_scale_hint} · order{" "}
            {metaQuery.data.sourcing_order.join(" → ")}
          </p>
          <p data-testid="lead-discovery-meta-honesty">
            tip /meta: {metaQuery.data.honesty}
          </p>
        </div>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">
          {getApiError(metaQuery.error)}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="lead-discovery-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
            if (selectedId) void detailQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh runs"}
        </Button>
        <span
          className="text-sm text-[var(--text-muted)]"
          data-testid="lead-discovery-count"
        >
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">
              {getApiError(listQuery.error)}
            </span>
          ) : (
            <>{listQuery.data?.length ?? 0} run(s)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="lead-discovery-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No discovery runs yet. Run one below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li key={row.id} className="px-1 py-1 text-sm">
              <button
                type="button"
                className={`w-full rounded px-2 py-2 text-start hover:bg-[var(--bg-tertiary)] ${
                  selectedId === row.id
                    ? "bg-[var(--bg-tertiary)] ring-1 ring-[var(--border-default)]"
                    : ""
                }`}
                data-testid="lead-discovery-row"
                onClick={() => loadRun(row)}
              >
                <span className="font-medium">{row.name}</span> · gov{" "}
                {row.government_hit_count} · provider {row.provider_hit_count} ·
                total {row.total_hits}
                <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                  {row.id} · gov_first {row.government_first_ok ? "ok" : "FAIL"}{" "}
                  · provider_key {row.provider_key || "—"}
                </span>
              </button>
            </li>
          ))
        )}
      </ul>

      {selectedId ? (
        detailQuery.isLoading ? (
          <Spinner className="h-5 w-5" />
        ) : detailQuery.isError ? (
          <p className="text-sm text-[var(--text-danger)]">
            {getApiError(detailQuery.error)}
          </p>
        ) : active ? (
          <div
            className="space-y-2 rounded border border-[var(--border-default)] p-3"
            data-testid="lead-discovery-detail"
          >
            <p className="text-xs font-semibold text-[var(--text-primary)]">
              Run {active.id} · gov {active.government_hit_count} then provider{" "}
              {active.provider_hit_count}
              {active.provider_key ? ` (${active.provider_key})` : ""}
            </p>
            <ul className="max-h-64 space-y-1 overflow-y-auto text-sm">
              {active.leads.length === 0 ? (
                <li className="text-[var(--text-muted)]">No leads in run.</li>
              ) : (
                active.leads.map((lead) => (
                  <li
                    key={lead.id}
                    className="font-mono text-xs"
                    data-testid="lead-discovery-lead"
                  >
                    <span className="font-sans font-medium text-[var(--text-primary)]">
                      {lead.company_name}
                    </span>{" "}
                    · {lead.source} · {lead.industry || "—"} ·{" "}
                    {lead.city || "—"} · emp {lead.employees_count ?? "—"}{" "}
                    <Link
                      href={buildEnrichmentHref({
                        company_name: lead.company_name,
                      })}
                      className="font-sans underline text-[var(--text-primary)]"
                      data-testid="lead-discovery-handoff-enrichment"
                    >
                      Enrich →
                    </Link>
                  </li>
                ))
              )}
            </ul>
          </div>
        ) : null
      ) : null}

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="lead-discovery-form"
        onSubmit={(e) => {
          e.preventDefault();
          const trimmed = name.trim();
          if (!trimmed) {
            toast({
              variant: "error",
              title: "Name required",
              description: "Provide a run name.",
            });
            return;
          }
          const lim = parseOptionalInt(limit) ?? 25;
          runMutation.mutate(
            {
              name: trimmed,
              industries: splitCsv(industries),
              cities: splitCsv(cities),
              employees_min: parseOptionalInt(employeesMin),
              employees_max: parseOptionalInt(employeesMax),
              limit: lim,
              use_provider_fallback: useFallback,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  variant: "success",
                  title: "Discovery complete",
                  description: `gov ${row.government_hit_count} · provider ${row.provider_hit_count} · total ${row.total_hits}`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Discovery failed",
                  description: getApiError(err),
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Run discovery (tip POST)
        </h2>
        <Input
          label="name"
          data-testid="lead-discovery-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={200}
        />
        <Input
          label="industries"
          data-testid="lead-discovery-industries"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
        />
        <Input
          label="cities"
          data-testid="lead-discovery-cities"
          value={cities}
          onChange={(e) => setCities(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="employees_min"
            data-testid="lead-discovery-employees-min"
            value={employeesMin}
            onChange={(e) => setEmployeesMin(e.target.value)}
            className="max-w-[10rem]"
          />
          <Input
            label="employees_max"
            data-testid="lead-discovery-employees-max"
            value={employeesMax}
            onChange={(e) => setEmployeesMax(e.target.value)}
            className="max-w-[10rem]"
          />
          <Input
            label="limit"
            data-testid="lead-discovery-limit"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="max-w-[8rem]"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            data-testid="lead-discovery-fallback"
            checked={useFallback}
            onChange={(e) => setUseFallback(e.target.checked)}
          />
          use_provider_fallback (Hub FakeSourceConnector in CI)
        </label>
        <Button
          type="submit"
          data-testid="lead-discovery-run"
          disabled={runMutation.isPending}
        >
          {runMutation.isPending ? "Discovering…" : "Run lead discovery"}
        </Button>
        <Link
          href="/gtm/market-sizing"
          className="ms-3 inline-flex text-sm underline text-[var(--text-primary)]"
          data-testid="lead-discovery-handoff-market-sizing"
        >
          ← Market Sizing
        </Link>
      </form>
    </div>
  );
}
