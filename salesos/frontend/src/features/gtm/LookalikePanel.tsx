"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useLookalikeDetail,
  useLookalikeList,
  useLookalikeMeta,
  useRunLookalikes,
} from "@/lib/hooks/lookalikeQueries";
import type { LookalikeRun } from "@/lib/api";
import { LOOKALIKE_HONESTY, LOOKALIKE_NON_GOALS } from "@/features/gtm/lookalikeHonesty";
import { buildEnrichmentHref, buildLeadDiscoveryHref } from "@/features/gtm/gtmHandoff";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

function parseOptionalInt(raw: string): number | null {
  const t = raw.trim();
  if (!t) return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return Math.trunc(n);
}

/**
 * FE-S11-04 — Lookalike Accounts against tip STORY-11-04 HTTP.
 * Deterministic won/lost fixtures. Not Production GO / RAG GO.
 */
export function LookalikePanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useLookalikeMeta();
  const listQuery = useLookalikeList();
  const runMutation = useRunLookalikes();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useLookalikeDetail(selectedId);

  const [name, setName] = useState("Pilot lookalike");
  const [companyName, setCompanyName] = useState("Acme Pilot Co");
  const [industry, setIndustry] = useState("technology");
  const [city, setCity] = useState("riyadh");
  const [employees, setEmployees] = useState("50");
  const [limit, setLimit] = useState("10");
  const [queryHydrated, setQueryHydrated] = useState(false);

  useEffect(() => {
    if (queryHydrated) return;
    const model = searchParams.get("model") ?? searchParams.get("run");
    if (model) setSelectedId(model);
    const c = searchParams.get("company_name");
    if (c?.trim()) setCompanyName(c.trim());
    const ind = searchParams.get("industry");
    if (ind?.trim()) setIndustry(ind.trim());
    const ct = searchParams.get("city");
    if (ct?.trim()) setCity(ct.trim());
    const emp = searchParams.get("employees_count");
    if (emp?.trim()) setEmployees(emp.trim());
    setQueryHydrated(true);
  }, [searchParams, queryHydrated]);

  function loadRun(row: LookalikeRun) {
    setSelectedId(row.id);
    setName(row.name);
    setCompanyName(row.seed.company_name ?? "");
    setIndustry(row.seed.industry ?? "");
    setCity(row.seed.city ?? "");
    setEmployees(row.seed.employees_count == null ? "" : String(row.seed.employees_count));
  }

  const active = detailQuery.data;

  return (
    <div className="space-y-4" data-testid="lookalike-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="lookalike-honesty"
      >
        {LOOKALIKE_HONESTY} Non-goals: {LOOKALIKE_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="lookalike-meta"
        >
          <p>
            {metaQuery.data.object} · {metaQuery.data.training} · features{" "}
            {(metaQuery.data.features ?? []).join(", ")}
          </p>
          <p data-testid="lookalike-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
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
          data-testid="lookalike-refresh"
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <span className="text-xs text-[var(--text-muted)]" data-testid="lookalike-count">
          {listQuery.data?.length ?? 0} model(s)
        </span>
      </div>

      <ul
        className="max-h-48 space-y-1 overflow-y-auto rounded border border-[var(--border-default)] p-2"
        data-testid="lookalike-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="text-xs text-[var(--text-muted)]">
            No lookalike runs yet. Submit a seed below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((row) => (
            <li key={row.id}>
              <button
                type="button"
                className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-[var(--bg-muted)] ${
                  selectedId === row.id ? "bg-[var(--bg-muted)] font-medium" : ""
                }`}
                data-testid="lookalike-row"
                onClick={() => loadRun(row)}
              >
                {row.name} · {row.seed.company_name ?? "—"} · {row.hit_count} hit(s) · won{" "}
                {row.trained_on_won}/lost {row.trained_on_lost}
              </button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-4"
        data-testid="lookalike-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim() || !companyName.trim()) {
            toast({
              title: "Seed required",
              description: "Provide name and company_name.",
              variant: "error",
            });
            return;
          }
          runMutation.mutate(
            {
              name: name.trim(),
              company_name: companyName.trim(),
              industry: industry.trim() || undefined,
              city: city.trim() || undefined,
              employees_count: parseOptionalInt(employees),
              limit: parseOptionalInt(limit) ?? 10,
            },
            {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  title: "Lookalike run complete",
                  description: `${row.hit_count} hit(s) · trained won ${row.trained_on_won} / lost ${row.trained_on_lost}`,
                  variant: "success",
                });
              },
              onError: (err) => {
                toast({
                  title: "Lookalike failed",
                  description: getApiError(err),
                  variant: "error",
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Run lookalikes (tip POST)
        </h2>
        <Input
          label="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          data-testid="lookalike-name"
        />
        <Input
          label="company_name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          data-testid="lookalike-company"
        />
        <Input
          label="industry"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          data-testid="lookalike-industry"
        />
        <Input
          label="city"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          data-testid="lookalike-city"
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="employees_count"
            value={employees}
            onChange={(e) => setEmployees(e.target.value)}
            className="max-w-[10rem]"
            data-testid="lookalike-employees"
          />
          <Input
            label="limit"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="max-w-[8rem]"
            data-testid="lookalike-limit"
          />
        </div>
        <Button type="submit" disabled={runMutation.isPending} data-testid="lookalike-run">
          {runMutation.isPending ? "Running…" : "Find lookalikes"}
        </Button>
      </form>

      {selectedId ? (
        <div
          className="space-y-2 rounded border border-[var(--border-default)] p-4"
          data-testid="lookalike-detail"
        >
          {detailQuery.isLoading ? (
            <Spinner />
          ) : detailQuery.isError ? (
            <p className="text-sm text-[var(--text-danger)]">{getApiError(detailQuery.error)}</p>
          ) : active ? (
            <>
              <p className="font-mono text-xs text-[var(--text-muted)]">
                model {active.id} · hits {active.hit_count} · trained won {active.trained_on_won} /
                lost {active.trained_on_lost} · v{active.schema_version}
              </p>
              <ul className="space-y-2 text-sm" data-testid="lookalike-hits">
                {active.hits.length === 0 ? (
                  <li className="text-[var(--text-muted)]">No hits.</li>
                ) : (
                  active.hits.map((h) => (
                    <li
                      key={h.company_id}
                      className="rounded border border-[var(--border-default)] p-2"
                      data-testid="lookalike-hit"
                    >
                      <div className="font-medium text-[var(--text-primary)]">
                        {h.company_name}{" "}
                        <span className="font-mono text-xs text-[var(--text-muted)]">
                          sim {h.similarity.toFixed(3)} · {h.outcome_affinity}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-muted)]">
                        {h.industry || "—"} · {h.city || "—"} · emp {h.employees_count ?? "—"} ·
                        matched {(h.matched_features ?? []).join(", ") || "—"}
                      </p>
                      <Link
                        href={buildEnrichmentHref({
                          company_name: h.company_name,
                        })}
                        className="text-xs underline text-[var(--text-primary)]"
                        data-testid="lookalike-handoff-enrichment"
                      >
                        Enrich →
                      </Link>
                    </li>
                  ))
                )}
              </ul>
              <Link
                href={buildLeadDiscoveryHref({
                  name: `${active.name} discovery`,
                  industries: active.seed.industry ?? "",
                  cities: active.seed.city ?? "",
                  employees_min: "",
                  employees_max: "",
                })}
                className="inline-flex text-sm underline text-[var(--text-primary)]"
                data-testid="lookalike-handoff-lead-discovery"
              >
                Open Lead Discovery with seed industry/city →
              </Link>
            </>
          ) : null}
        </div>
      ) : null}

      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/gtm/enrichment" className="underline">
          /gtm/enrichment
        </Link>
        {" · "}
        <Link href="/gtm" className="underline">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
