"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useComputeMarketSizing,
  useMarketSizingDetail,
  useMarketSizingList,
  useMarketSizingMeta,
} from "@/lib/hooks/marketSizingQueries";
import type { MarketSizingSnapshot } from "@/lib/api";
import {
  MARKET_SIZING_HONESTY,
  MARKET_SIZING_NON_GOALS,
} from "@/features/gtm/marketSizingHonesty";

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

function pctOf(part: number, whole: number): number {
  if (!whole || whole <= 0) return 0;
  return Math.max(0, Math.min(100, (part / whole) * 100));
}

function NestedBands({ row }: { row: MarketSizingSnapshot }) {
  const base = Math.max(row.universe_size, row.tam, 1);
  return (
    <div
      className="space-y-2 rounded border border-[var(--border-default)] p-3"
      data-testid="market-sizing-bands"
    >
      <p className="text-xs font-semibold text-[var(--text-primary)]">
        Nested bands (SOM ≤ SAM ≤ TAM ≤ universe) — tip snapshot {row.id}
      </p>
      {(
        [
          ["Universe", row.universe_size, "var(--text-muted)"],
          ["TAM", row.tam, "var(--muhide-orange)"],
          ["SAM", row.sam, "#2563eb"],
          ["SOM", row.som, "#16a34a"],
        ] as const
      ).map(([label, value, color]) => (
        <div
          key={label}
          data-testid={`market-sizing-band-${label.toLowerCase()}`}
        >
          <div className="mb-0.5 flex justify-between text-xs text-[var(--text-muted)]">
            <span>{label}</span>
            <span className="font-mono">{value}</span>
          </div>
          <div className="h-2 overflow-hidden rounded bg-[var(--bg-tertiary)]">
            <div
              className="h-full rounded"
              style={{
                width: `${pctOf(value, base)}%`,
                backgroundColor: color,
              }}
            />
          </div>
        </div>
      ))}
      <p className="font-mono text-xs text-[var(--text-muted)]">
        invariant {row.invariant_ok ? "ok" : "FAIL"} · hint{" "}
        {row.dataset_scale_hint} (scale hint only — live 141221 not claimed)
      </p>
    </div>
  );
}

/**
 * FE-S11-02 / FE-S11-02b — TAM/SAM/SOM Market Sizing against tip STORY-11-02 HTTP.
 * Detail GET + nested bands polish. Not Production GO / RAG GO.
 */
export function MarketSizingPanel() {
  const { toast } = useToast();
  const metaQuery = useMarketSizingMeta();
  const listQuery = useMarketSizingList();
  const computeMutation = useComputeMarketSizing();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useMarketSizingDetail(selectedId);

  const [name, setName] = useState("Pilot market");
  const [industries, setIndustries] = useState("technology, software");
  const [cities, setCities] = useState("riyadh, jeddah");
  const [employeesMin, setEmployeesMin] = useState("10");
  const [employeesMax, setEmployeesMax] = useState("500");

  function loadCriteria(row: MarketSizingSnapshot) {
    setSelectedId(row.id);
    setName(row.name);
    setIndustries((row.criteria.industries ?? []).join(", "));
    setCities((row.criteria.cities ?? []).join(", "));
    setEmployeesMin(
      row.criteria.employees_min == null
        ? ""
        : String(row.criteria.employees_min),
    );
    setEmployeesMax(
      row.criteria.employees_max == null
        ? ""
        : String(row.criteria.employees_max),
    );
  }

  const activeDetail = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="market-sizing-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="market-sizing-honesty"
      >
        {MARKET_SIZING_HONESTY} Non-goals: {MARKET_SIZING_NON_GOALS.join("; ")}.
        Not Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="market-sizing-meta"
        >
          <p>
            scale_hint {metaQuery.data.dataset_scale_hint} ·{" "}
            {metaQuery.data.invariant}
          </p>
          <p data-testid="market-sizing-meta-honesty">
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
          data-testid="market-sizing-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
            if (selectedId) void detailQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh snapshots"}
        </Button>
        <span
          className="text-sm text-[var(--text-muted)]"
          data-testid="market-sizing-count"
        >
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">
              {getApiError(listQuery.error)}
            </span>
          ) : (
            <>{listQuery.data?.length ?? 0} snapshot(s)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="market-sizing-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No market sizing snapshots yet. Compute one below (tip POST).
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
                data-testid="market-sizing-row"
                onClick={() => loadCriteria(row)}
              >
                <span className="font-medium">{row.name}</span> · TAM {row.tam}{" "}
                · SAM {row.sam} · SOM {row.som}
                <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                  {row.id} · universe {row.universe_size} · hint{" "}
                  {row.dataset_scale_hint} · invariant{" "}
                  {row.invariant_ok ? "ok" : "FAIL"} · click → tip GET detail
                </span>
              </button>
            </li>
          ))
        )}
      </ul>

      {selectedId ? (
        detailQuery.isLoading ? (
          <Spinner
            className="h-5 w-5"
            data-testid="market-sizing-detail-loading"
          />
        ) : detailQuery.isError ? (
          <p
            className="text-sm text-[var(--text-danger)]"
            data-testid="market-sizing-detail-error"
          >
            {getApiError(detailQuery.error)}
          </p>
        ) : activeDetail ? (
          <NestedBands row={activeDetail} />
        ) : null
      ) : null}

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="market-sizing-form"
        onSubmit={(e) => {
          e.preventDefault();
          const trimmed = name.trim();
          if (!trimmed) {
            toast({
              variant: "error",
              title: "Name required",
              description: "Provide a snapshot name.",
            });
            return;
          }
          computeMutation.mutate(
            {
              name: trimmed,
              industries: splitCsv(industries),
              cities: splitCsv(cities),
              employees_min: parseOptionalInt(employeesMin),
              employees_max: parseOptionalInt(employeesMax),
              id: selectedId ?? undefined,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  variant: "success",
                  title: "Market sized",
                  description: `TAM ${row.tam} · SAM ${row.sam} · SOM ${row.som}`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Compute failed",
                  description: getApiError(err),
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Compute TAM / SAM / SOM (tip POST)
          {selectedId ? (
            <span className="ms-2 font-mono text-xs font-normal text-[var(--text-muted)]">
              upsert id {selectedId}
            </span>
          ) : null}
        </h2>
        <Input
          label="name"
          data-testid="market-sizing-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={200}
        />
        <Input
          label="industries (comma-separated → TAM band)"
          data-testid="market-sizing-industries"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
        />
        <Input
          label="cities (comma-separated → SAM band)"
          data-testid="market-sizing-cities"
          value={cities}
          onChange={(e) => setCities(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="employees_min (SOM)"
            data-testid="market-sizing-employees-min"
            value={employeesMin}
            onChange={(e) => setEmployeesMin(e.target.value)}
            className="max-w-[10rem]"
          />
          <Input
            label="employees_max (SOM)"
            data-testid="market-sizing-employees-max"
            value={employeesMax}
            onChange={(e) => setEmployeesMax(e.target.value)}
            className="max-w-[10rem]"
          />
        </div>
        <Button
          type="submit"
          data-testid="market-sizing-compute"
          disabled={computeMutation.isPending}
        >
          {computeMutation.isPending ? "Computing…" : "Compute market size"}
        </Button>
      </form>
    </div>
  );
}
