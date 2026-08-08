"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCreateIcpProfile,
  useIcpMeta,
  useIcpProfile,
  useIcpProfiles,
  useScoreIcpProfile,
  useUpdateIcpProfile,
} from "@/lib/hooks/icpProfilesQueries";
import type { ICPProfile, ICPScoreResult } from "@/lib/api";
import { ICP_PROFILES_HONESTY, ICP_PROFILES_NON_GOALS } from "@/features/gtm/icpProfilesHonesty";
import { buildEnrichmentHref, buildLeadDiscoveryHref } from "@/features/gtm/gtmHandoff";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
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

function parseOptionalFloat(raw: string, fallback: number): number {
  const t = raw.trim();
  if (!t) return fallback;
  const n = Number(t);
  return Number.isFinite(n) ? n : fallback;
}

/**
 * FE-S11-01 — ICP Profiles against tip STORY-11-01 HTTP.
 * Versioned in-memory ICP + deterministic score. Not Production GO / RAG GO.
 */
export function IcpProfilesPanel() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const metaQuery = useIcpMeta();
  const listQuery = useIcpProfiles();
  const createMutation = useCreateIcpProfile();
  const updateMutation = useUpdateIcpProfile();
  const scoreMutation = useScoreIcpProfile();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useIcpProfile(selectedId);
  const [hydrated, setHydrated] = useState(false);

  const [name, setName] = useState("Pilot ICP");
  const [description, setDescription] = useState("");
  const [industries, setIndustries] = useState("technology");
  const [cities, setCities] = useState("riyadh");
  const [employeesMin, setEmployeesMin] = useState("10");
  const [employeesMax, setEmployeesMax] = useState("500");
  const [titles, setTitles] = useState("ceo, vp sales");
  const [keywords, setKeywords] = useState("saas, b2b");
  const [wIndustry, setWIndustry] = useState("1");
  const [wCity, setWCity] = useState("1");
  const [wEmployees, setWEmployees] = useState("1");
  const [wTitles, setWTitles] = useState("0.5");
  const [wKeywords, setWKeywords] = useState("0.5");
  const [isActive, setIsActive] = useState(true);

  const [scoreIndustry, setScoreIndustry] = useState("technology");
  const [scoreCity, setScoreCity] = useState("riyadh");
  const [scoreEmployees, setScoreEmployees] = useState("120");
  const [scoreTitle, setScoreTitle] = useState("VP Sales");
  const [scoreName, setScoreName] = useState("Acme Co");
  const [scoreKeywords, setScoreKeywords] = useState("saas b2b");
  const [lastScore, setLastScore] = useState<ICPScoreResult | null>(null);

  useEffect(() => {
    if (hydrated) return;
    const id = searchParams.get("profile");
    if (id) setSelectedId(id);
    setHydrated(true);
  }, [searchParams, hydrated]);

  function loadProfile(row: ICPProfile) {
    setSelectedId(row.id);
    setName(row.name);
    setDescription(row.description ?? "");
    setIndustries((row.criteria.industries ?? []).join(", "));
    setCities((row.criteria.cities ?? []).join(", "));
    setEmployeesMin(row.criteria.employees_min == null ? "" : String(row.criteria.employees_min));
    setEmployeesMax(row.criteria.employees_max == null ? "" : String(row.criteria.employees_max));
    setTitles((row.criteria.titles ?? []).join(", "));
    setKeywords((row.criteria.keywords ?? []).join(", "));
    setWIndustry(String(row.weights.industry));
    setWCity(String(row.weights.city));
    setWEmployees(String(row.weights.employees));
    setWTitles(String(row.weights.titles));
    setWKeywords(String(row.weights.keywords));
    setIsActive(row.is_active);
    setLastScore(null);
  }

  useEffect(() => {
    const row = detailQuery.data;
    if (!row || !hydrated) return;
    if (selectedId !== row.id) return;
    setName(row.name);
    setDescription(row.description ?? "");
    setIndustries((row.criteria.industries ?? []).join(", "));
    setCities((row.criteria.cities ?? []).join(", "));
    setEmployeesMin(row.criteria.employees_min == null ? "" : String(row.criteria.employees_min));
    setEmployeesMax(row.criteria.employees_max == null ? "" : String(row.criteria.employees_max));
    setTitles((row.criteria.titles ?? []).join(", "));
    setKeywords((row.criteria.keywords ?? []).join(", "));
    setWIndustry(String(row.weights.industry));
    setWCity(String(row.weights.city));
    setWEmployees(String(row.weights.employees));
    setWTitles(String(row.weights.titles));
    setWKeywords(String(row.weights.keywords));
    setIsActive(row.is_active);
// eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detailQuery.data?.id, detailQuery.data?.schema_version, selectedId, hydrated]);

  function bodyFromForm() {
    return {
      name: name.trim(),
      description: description.trim(),
      industries: splitCsv(industries),
      cities: splitCsv(cities),
      employees_min: parseOptionalInt(employeesMin),
      employees_max: parseOptionalInt(employeesMax),
      titles: splitCsv(titles),
      keywords: splitCsv(keywords),
      weights: {
        industry: parseOptionalFloat(wIndustry, 1),
        city: parseOptionalFloat(wCity, 1),
        employees: parseOptionalFloat(wEmployees, 1),
        titles: parseOptionalFloat(wTitles, 0.5),
        keywords: parseOptionalFloat(wKeywords, 0.5),
      },
      is_active: isActive,
    };
  }

  return (
    <div className="space-y-4" data-testid="icp-profiles-panel">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="icp-profiles-honesty"
      >
        {ICP_PROFILES_HONESTY} Non-goals: {ICP_PROFILES_NON_GOALS.join("; ")}. Not Production GO /
        RAG GO.
      </p>

      {metaQuery.data ? (
        <div
          className="space-y-1 font-mono text-xs text-[var(--text-muted)]"
          data-testid="icp-profiles-meta"
        >
          <p>
            {metaQuery.data.object} · {metaQuery.data.versioning} · {metaQuery.data.scoring}
          </p>
          <p data-testid="icp-profiles-meta-honesty">tip /meta: {metaQuery.data.honesty}</p>
        </div>
      ) : metaQuery.isError ? (
        <p className="text-sm text-[var(--text-danger)]">{getApiError(metaQuery.error)}</p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="icp-profiles-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
            void metaQuery.refetch();
            if (selectedId) void detailQuery.refetch();
          }}
        >
          {listQuery.isFetching ? "Refreshing…" : "Refresh profiles"}
        </Button>
        <span className="text-sm text-[var(--text-muted)]" data-testid="icp-profiles-count">
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">{getApiError(listQuery.error)}</span>
          ) : (
            <>{listQuery.data?.length ?? 0} profile(s)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="icp-profiles-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No ICP profiles yet. Create one below (tip POST).
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
                data-testid="icp-profiles-row"
                onClick={() => loadProfile(row)}
              >
                <span className="font-medium">{row.name}</span> · v{row.schema_version} ·{" "}
                {row.is_active ? "active" : "inactive"}
                <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                  {row.id} · industries {(row.criteria.industries ?? []).join(",") || "—"}
                </span>
              </button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="icp-profiles-form"
        onSubmit={(e) => {
          e.preventDefault();
          const body = bodyFromForm();
          if (!body.name) {
            toast({
              variant: "error",
              title: "Name required",
              description: "Provide an ICP profile name.",
            });
            return;
          }
          if (selectedId) {
            updateMutation.mutate(
              { profileId: selectedId, body },
              {
                onSuccess: (row) => {
                  toast({
                    variant: "success",
                    title: "ICP updated",
                    description: `${row.name} · v${row.schema_version}`,
                  });
                },
                onError: (err) => {
                  toast({
                    variant: "error",
                    title: "Update failed",
                    description: getApiError(err),
                  });
                },
              }
            );
          } else {
            createMutation.mutate(body, {
              onSuccess: (row) => {
                setSelectedId(row.id);
                toast({
                  variant: "success",
                  title: "ICP created",
                  description: `${row.name} · v${row.schema_version}`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Create failed",
                  description: getApiError(err),
                });
              },
            });
          }
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          {selectedId ? "Update ICP (tip PUT)" : "Create ICP (tip POST)"}
          {selectedId ? (
            <span className="ms-2 font-mono text-xs font-normal text-[var(--text-muted)]">
              {selectedId}
            </span>
          ) : null}
        </h2>
        <Input
          label="name"
          data-testid="icp-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={200}
        />
        <Input
          label="description"
          data-testid="icp-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Input
          label="industries"
          data-testid="icp-industries"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
        />
        <Input
          label="cities"
          data-testid="icp-cities"
          value={cities}
          onChange={(e) => setCities(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="employees_min"
            data-testid="icp-employees-min"
            value={employeesMin}
            onChange={(e) => setEmployeesMin(e.target.value)}
            className="max-w-[10rem]"
          />
          <Input
            label="employees_max"
            data-testid="icp-employees-max"
            value={employeesMax}
            onChange={(e) => setEmployeesMax(e.target.value)}
            className="max-w-[10rem]"
          />
        </div>
        <Input
          label="titles"
          data-testid="icp-titles"
          value={titles}
          onChange={(e) => setTitles(e.target.value)}
        />
        <Input
          label="keywords"
          data-testid="icp-keywords"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="w.industry"
            data-testid="icp-w-industry"
            value={wIndustry}
            onChange={(e) => setWIndustry(e.target.value)}
            className="max-w-[8rem]"
          />
          <Input
            label="w.city"
            data-testid="icp-w-city"
            value={wCity}
            onChange={(e) => setWCity(e.target.value)}
            className="max-w-[8rem]"
          />
          <Input
            label="w.employees"
            data-testid="icp-w-employees"
            value={wEmployees}
            onChange={(e) => setWEmployees(e.target.value)}
            className="max-w-[8rem]"
          />
          <Input
            label="w.titles"
            data-testid="icp-w-titles"
            value={wTitles}
            onChange={(e) => setWTitles(e.target.value)}
            className="max-w-[8rem]"
          />
          <Input
            label="w.keywords"
            data-testid="icp-w-keywords"
            value={wKeywords}
            onChange={(e) => setWKeywords(e.target.value)}
            className="max-w-[8rem]"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            data-testid="icp-active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          is_active
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="submit"
            data-testid="icp-save"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending
              ? "Saving…"
              : selectedId
                ? "Update profile"
                : "Create profile"}
          </Button>
          {selectedId ? (
            <Button
              type="button"
              data-testid="icp-new"
              onClick={() => {
                setSelectedId(null);
                setLastScore(null);
              }}
            >
              New profile
            </Button>
          ) : null}
          <Link
            href={buildLeadDiscoveryHref({
              name: name.trim() ? `${name.trim()} discovery` : "Pilot discovery",
              industries,
              cities,
              employees_min: employeesMin,
              employees_max: employeesMax,
            })}
            className="text-sm underline text-[var(--text-primary)]"
            data-testid="icp-handoff-lead-discovery"
          >
            Open Lead Discovery with these filters →
          </Link>
          <Link
            href={buildEnrichmentHref({
              company_name: name.trim() || "Pilot ICP company",
            })}
            className="text-sm underline text-[var(--text-primary)]"
            data-testid="icp-handoff-enrichment"
          >
            Enrich a seed company →
          </Link>
        </div>
      </form>

      {selectedId ? (
        <form
          className="space-y-3 rounded border border-[var(--border-default)] p-3"
          data-testid="icp-score-form"
          onSubmit={(e) => {
            e.preventDefault();
            scoreMutation.mutate(
              {
                profileId: selectedId,
                body: {
                  industry: scoreIndustry.trim(),
                  city: scoreCity.trim(),
                  employees_count: parseOptionalInt(scoreEmployees),
                  title: scoreTitle.trim(),
                  name: scoreName.trim(),
                  keywords: scoreKeywords.trim(),
                },
              },
              {
                onSuccess: (row) => {
                  setLastScore(row);
                  toast({
                    variant: "success",
                    title: "Scored",
                    description: `fit ${(row.fit_ratio * 100).toFixed(0)}% · ${row.score}/${row.max_score}`,
                  });
                },
                onError: (err) => {
                  toast({
                    variant: "error",
                    title: "Score failed",
                    description: getApiError(err),
                  });
                },
              }
            );
          }}
        >
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Score company (tip POST …/score) — deterministic fit
          </h2>
          <Input
            label="company name"
            data-testid="icp-score-name"
            value={scoreName}
            onChange={(e) => setScoreName(e.target.value)}
          />
          <Input
            label="industry"
            data-testid="icp-score-industry"
            value={scoreIndustry}
            onChange={(e) => setScoreIndustry(e.target.value)}
          />
          <Input
            label="city"
            data-testid="icp-score-city"
            value={scoreCity}
            onChange={(e) => setScoreCity(e.target.value)}
          />
          <div className="flex flex-wrap gap-3">
            <Input
              label="employees_count"
              data-testid="icp-score-employees"
              value={scoreEmployees}
              onChange={(e) => setScoreEmployees(e.target.value)}
              className="max-w-[10rem]"
            />
            <Input
              label="title"
              data-testid="icp-score-title"
              value={scoreTitle}
              onChange={(e) => setScoreTitle(e.target.value)}
              className="max-w-[14rem]"
            />
          </div>
          <Input
            label="keywords (free text)"
            data-testid="icp-score-keywords"
            value={scoreKeywords}
            onChange={(e) => setScoreKeywords(e.target.value)}
          />
          <Button type="submit" data-testid="icp-score-run" disabled={scoreMutation.isPending}>
            {scoreMutation.isPending ? "Scoring…" : "Score against ICP"}
          </Button>
          {lastScore ? (
            <div
              className="font-mono text-xs text-[var(--text-muted)]"
              data-testid="icp-score-result"
            >
              score {lastScore.score}/{lastScore.max_score} · fit_ratio{" "}
              {lastScore.fit_ratio.toFixed(3)} · matched {JSON.stringify(lastScore.matched)} ·
              profile v{lastScore.schema_version}
            </div>
          ) : null}
        </form>
      ) : null}
    </div>
  );
}
