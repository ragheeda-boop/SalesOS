"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

type ICPProfile = {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  schema_version: number;
  criteria: {
    industries: string[];
    cities: string[];
    employees_min?: number | null;
    employees_max?: number | null;
    titles?: string[];
    keywords?: string[];
  };
};

type ICPListResponse = {
  profiles: ICPProfile[];
  count: number;
};

type ICPScoreResponse = {
  profile_id: string;
  schema_version: number;
  score: number;
  max_score: number;
  fit_ratio: number;
  matched: Record<string, boolean>;
  company: Record<string, unknown>;
};

export default function V3ICPPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [industries, setIndustries] = useState("construction, financial-services");
  const [cities, setCities] = useState("Riyadh, Jeddah");
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [companyIndustry, setCompanyIndustry] = useState("");
  const [companyCity, setCompanyCity] = useState("");
  const [companyEmployees, setCompanyEmployees] = useState("");
  const [companyTitle, setCompanyTitle] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["icp", "profiles"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/icp/profiles", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as ICPListResponse;
    },
    enabled: ready && hasToken,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post(
        "/api/v1/icp/profiles",
        {
          name,
          description: "Created from v3 ICP admin",
          criteria: {
            industries: industries.split(",").map((s) => s.trim()).filter(Boolean),
            cities: cities.split(",").map((s) => s.trim()).filter(Boolean),
          },
          is_active: true,
        },
        { headers: { "X-Tenant-Id": getTenantId() } },
      );
      return res.data;
    },
    onSuccess: () => {
      setName("");
      queryClient.invalidateQueries({ queryKey: ["icp", "profiles"] });
    },
  });

  const scoreMutation = useMutation({
    mutationFn: async (profileId: string) => {
      const response = await apiClient.post<ICPScoreResponse>(
        `/api/v1/icp/profiles/${encodeURIComponent(profileId)}/score`,
        {
          name: companyName,
          industry: companyIndustry,
          city: companyCity,
          employees_count: companyEmployees.trim() ? Number(companyEmployees) : null,
          title: companyTitle,
        },
        { headers: { "X-Tenant-Id": getTenantId() } },
      );
      return response.data;
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/icp" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const profiles = data?.profiles ?? [];

  return (
    <>
      <PageHeader
        title="ICP Profiles"
        description="Tenant-scoped Ideal Customer Profile definitions and deterministic firmographic matching"
      />
      <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
        <h2 className="mb-3 text-sm font-semibold">Create profile</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <input
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Profile name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Industries (comma-separated)"
            value={industries}
            onChange={(e) => setIndustries(e.target.value)}
          />
          <input
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Cities (comma-separated)"
            value={cities}
            onChange={(e) => setCities(e.target.value)}
          />
        </div>
        <button
          disabled={!name.trim() || createMutation.isPending}
          onClick={() => createMutation.mutate()}
          className="mt-3 rounded-md bg-[var(--accent-primary)] px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {createMutation.isPending ? "Creating…" : "Create ICP profile"}
        </button>
      </div>
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-hover)]"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>
      {profiles.length === 0 ? (
        <EmptyState
          title="No ICP profiles"
          description="Create a profile to enable grounded ICP scoring for this tenant."
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
          <table className="w-full text-sm">
            <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">Active</th>
                <th className="px-4 py-3">Industries</th>
                <th className="px-4 py-3">Cities</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-default)]">
              {profiles.map((p) => (
                <tr key={p.id} className="hover:bg-[var(--bg-hover)]">
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3">v{p.schema_version}</td>
                  <td className="px-4 py-3">{p.is_active ? "Yes" : "No"}</td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">
                    {(p.criteria?.industries ?? []).join(", ") || "—"}
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">
                    {(p.criteria?.cities ?? []).join(", ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <section className="mt-6 rounded-lg border border-[var(--border-default)] p-4" aria-labelledby="icp-score-title">
        <h2 id="icp-score-title" className="text-sm font-semibold">Score a company snapshot</h2>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          Rule-based matching against the saved profile and the values entered here. It does not look up external data or predict sales outcomes.
        </p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <label className="space-y-1 text-xs text-[var(--text-secondary)]">
            <span>Profile</span>
            <select
              aria-label="ICP profile"
              className="w-full rounded border border-[var(--border-default)] px-3 py-2 text-sm"
              value={selectedProfileId || profiles[0]?.id || ""}
              onChange={(event) => setSelectedProfileId(event.target.value)}
            >
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>{profile.name}</option>
              ))}
            </select>
          </label>
          <input
            aria-label="Company name"
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Company name"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
          />
          <input
            aria-label="Company industry"
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Industry"
            value={companyIndustry}
            onChange={(event) => setCompanyIndustry(event.target.value)}
          />
          <input
            aria-label="Company city"
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="City"
            value={companyCity}
            onChange={(event) => setCompanyCity(event.target.value)}
          />
          <input
            aria-label="Company employee count"
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Employee count"
            inputMode="numeric"
            value={companyEmployees}
            onChange={(event) => setCompanyEmployees(event.target.value.replace(/[^0-9]/g, ""))}
          />
          <input
            aria-label="Contact title"
            className="rounded border border-[var(--border-default)] px-3 py-2 text-sm"
            placeholder="Contact title (optional)"
            value={companyTitle}
            onChange={(event) => setCompanyTitle(event.target.value)}
          />
        </div>
        <button
          type="button"
          disabled={!profiles.length || scoreMutation.isPending}
          onClick={() => scoreMutation.mutate(selectedProfileId || profiles[0]?.id || "")}
          className="mt-3 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm text-[var(--text-primary)] disabled:opacity-50"
        >
          {scoreMutation.isPending ? "Scoring…" : "Calculate profile fit"}
        </button>
        {scoreMutation.isError ? (
          <p className="mt-3 text-sm text-[var(--status-danger,#dc2626)]" role="alert">
            {scoreMutation.error instanceof Error ? scoreMutation.error.message : "Could not score company"}
          </p>
        ) : null}
        {scoreMutation.data ? (
          <div className="mt-4 rounded-md bg-[var(--bg-secondary)] p-3" aria-live="polite" data-testid="icp-score-result">
            <p className="text-sm font-medium text-[var(--text-primary)]">
              Fit: {Math.round(scoreMutation.data.fit_ratio * 100)}% · {scoreMutation.data.score} / {scoreMutation.data.max_score} points
            </p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Profile version {scoreMutation.data.schema_version}</p>
            <ul className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--text-secondary)]">
              {Object.entries(scoreMutation.data.matched)
                .filter(([criterion]) => {
                  const profile = profiles.find((item) => item.id === scoreMutation.data?.profile_id);
                  const criteria = profile?.criteria;
                  if (!criteria) return criterion === "empty_profile";
                  if (criterion === "industry") return criteria.industries.length > 0;
                  if (criterion === "city") return criteria.cities.length > 0;
                  if (criterion === "employees") {
                    return criteria.employees_min != null || criteria.employees_max != null;
                  }
                  if (criterion === "titles") return Boolean(criteria.titles?.length);
                  if (criterion === "keywords") return Boolean(criteria.keywords?.length);
                  return criterion === "empty_profile";
                })
                .map(([criterion, matched]) => (
                <li key={criterion} className="rounded border border-[var(--border-default)] px-2 py-1">
                  {criterion.replace(/_/g, " ")}: {matched ? "match" : "no match"}
                </li>
                ))}
            </ul>
          </div>
        ) : null}
      </section>
    </>
  );
}
