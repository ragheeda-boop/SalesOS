"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

type Person = {
  id: string;
  slug: string;
  canonical_name: string;
  email: string | null;
  phone: string | null;
  company_global_id: string | null;
  job_title: string | null;
  status: string;
  created_at: string;
};

export default function V3DataPeoplePage() {
  const { ready, hasToken } = useAccessToken();
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["masterData", "people", page],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-people", {
        params: { page, page_size: pageSize },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as {
        items: Person[];
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
      };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/data/people" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const people = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  if (people.length === 0)
    return (
      <>
        <PageHeader
          title="Global People"
          description={`${total.toLocaleString()} canonical records`}
        />
        <EmptyState
          title="No people found"
          description="There are no canonical person records to display."
        />
      </>
    );

  return (
    <>
      <PageHeader title="Global People" description={`${total.toLocaleString()} records`} />
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-hover)]"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>
      <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
        <table className="w-full text-sm">
          <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Job title</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Company Global ID</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {people.map((p) => (
              <tr key={p.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">{p.canonical_name || "Unnamed"}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{p.job_title || "-"}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{p.email || "-"}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{p.company_global_id || "-"}</td>
                <td className="px-4 py-3">{p.status || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3 text-sm">
        <span className="text-[var(--text-muted)]">
          Page {page} of {pageCount} · {people.length.toLocaleString()} shown on this page
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            disabled={page <= 1}
            className="rounded-md border border-[var(--border-default)] px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => setPage((current) => current + 1)}
            disabled={!data?.has_next}
            className="rounded-md border border-[var(--border-default)] px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}
