"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

type ERStats = {
  total_golden_records: number;
  open_conflicts: number;
};

type Conflict = {
  id: string;
  golden_record_id: string;
  field_name: string;
  source_a_value: string | null;
  source_a_source: string;
  source_b_value: string | null;
  source_b_source: string;
  resolution_strategy: string | null;
  status: string;
  created_at: string;
};

type Match = {
  id: string;
  global_entity_id: string | null;
  source_a_id: string;
  source_b_id: string;
  match_score: number;
  match_method: string;
  match_signals: unknown[];
  match_status: string;
  created_at: string;
};

type PageResult<T> = { items: T[]; total: number };

export default function V3DataERPage() {
  const { ready, hasToken } = useAccessToken();
  const tenantHeaders = { "X-Tenant-Id": getTenantId() };

  const stats = useQuery({
    queryKey: ["er", "stats"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/entity-resolution/stats", {
        headers: tenantHeaders,
      });
      return res.data as ERStats;
    },
    enabled: ready && hasToken,
  });

  const conflicts = useQuery({
    queryKey: ["er", "conflicts"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/entity-resolution/conflicts", {
        params: { page_size: 20 },
        headers: tenantHeaders,
      });
      return res.data as PageResult<Conflict>;
    },
    enabled: ready && hasToken,
  });

  const matches = useQuery({
    queryKey: ["er", "matches"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/entity-resolution/matches", {
        params: { page: 1, page_size: 20 },
        headers: tenantHeaders,
      });
      return res.data as PageResult<Match>;
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/data/er" />;
  if (stats.isLoading || conflicts.isLoading || matches.isLoading) return <LoadingState />;

  if (stats.isError || conflicts.isError || matches.isError) {
    const error = stats.error ?? conflicts.error ?? matches.error;
    return (
      <ErrorState
        title="Could not load entity-resolution data"
        description={error instanceof Error ? error.message : "Request failed"}
        onRetry={() => {
          void Promise.all([stats.refetch(), conflicts.refetch(), matches.refetch()]);
        }}
      />
    );
  }

  const statsData = stats.data;
  const conflictItems = conflicts.data?.items ?? [];
  const matchItems = matches.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Entity Resolution"
        description="Golden records, conflicts, and match evidence"
      />

      {statsData ? (
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-[var(--border-default)] p-4">
            <div className="text-2xl font-bold text-[var(--text-link)]">
              {statsData.total_golden_records.toLocaleString()}
            </div>
            <div className="text-sm text-[var(--text-muted)]">Golden Records</div>
          </div>
          <div className="rounded-lg border border-[var(--border-default)] p-4">
            <div className="text-2xl font-bold text-[var(--status-warning-text)]">
              {statsData.open_conflicts.toLocaleString()}
            </div>
            <div className="text-sm text-[var(--text-muted)]">Open Conflicts</div>
          </div>
        </div>
      ) : null}

      <section className="mb-8">
        <h2 className="mb-2 text-sm font-medium text-[var(--text-primary)]">
          Recent Conflicts ({(conflicts.data?.total ?? 0).toLocaleString()})
        </h2>
        {conflictItems.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]">No conflicts.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-[var(--border-default)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3">Golden Record</th>
                  <th className="px-4 py-3">Field</th>
                  <th className="px-4 py-3">Source A value</th>
                  <th className="px-4 py-3">Source B value</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {conflictItems.map((conflict) => (
                  <tr key={conflict.id} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3 font-mono text-xs">{conflict.golden_record_id}</td>
                    <td className="px-4 py-3 font-medium">{conflict.field_name}</td>
                    <td className="px-4 py-3">
                      <div>{conflict.source_a_value || "-"}</div>
                      <div className="mt-1 text-xs text-[var(--text-muted)]">
                        {conflict.source_a_source}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{conflict.source_b_value || "-"}</div>
                      <div className="mt-1 text-xs text-[var(--text-muted)]">
                        {conflict.source_b_source}
                      </div>
                    </td>
                    <td className="px-4 py-3">{conflict.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-[var(--text-primary)]">
          Recent Matches ({(matches.data?.total ?? 0).toLocaleString()})
        </h2>
        {matchItems.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]">No matches.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-[var(--border-default)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3">Source A</th>
                  <th className="px-4 py-3">Source B</th>
                  <th className="px-4 py-3">Match score</th>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {matchItems.map((match) => (
                  <tr key={match.id} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3 font-mono text-xs">{match.source_a_id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{match.source_b_id}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`font-medium ${
                          match.match_score >= 0.9
                            ? "text-green-600"
                            : match.match_score >= 0.7
                              ? "text-yellow-600"
                              : "text-red-600"
                        }`}
                      >
                        {(match.match_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{match.match_method}</td>
                    <td className="px-4 py-3">{match.match_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
