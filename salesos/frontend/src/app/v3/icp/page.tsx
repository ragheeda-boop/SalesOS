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
  };
};

type ICPListResponse = {
  profiles: ICPProfile[];
  count: number;
};

export default function V3ICPPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [industries, setIndustries] = useState("construction, financial-services");
  const [cities, setCities] = useState("Riyadh, Jeddah");

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
        description="Ideal Customer Profile definitions — tenant-scoped, evidence-backed scoring"
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
    </>
  );
}
