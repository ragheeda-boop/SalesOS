"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { RefreshCw, FileText } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

type SourceFile = {
  id: string;
  filename: string;
  file_hash_sha256: string;
  total_rows: number;
  uploaded_at: string;
  source_system: string;
  mime_type: string;
  status: string;
};

export default function V3DataImportsPage() {
  const { ready, hasToken } = useAccessToken();
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["masterData", "sourceFiles", page],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/source-files", {
        params: { page, page_size: pageSize },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as {
        items: SourceFile[];
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
      };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/data/imports" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const files = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  if (files.length === 0)
    return (
      <>
        <PageHeader title="Source Files & Imports" description="Manage ingested data files" />
        <EmptyState title="No source files" description="Import data files to see them here." />
      </>
    );

  return (
    <>
      <PageHeader title="Source Files & Imports" description={`${total.toLocaleString()} files`} />
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
              <th className="px-4 py-3">Filename</th>
              <th className="px-4 py-3">Rows</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Imported</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {files.map((f) => (
              <tr key={f.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">
                  <span className="inline-flex items-center gap-1.5">
                    <FileText className="h-4 w-4 text-[var(--text-muted)]" />
                    {f.filename}
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {f.total_rows.toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${f.status === "imported" ? "bg-green-100 text-green-700" : f.status === "error" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-700"}`}
                  >
                    {f.status || "unknown"}
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {f.uploaded_at ? new Date(f.uploaded_at).toLocaleString() : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3 text-sm">
        <span className="text-[var(--text-muted)]">
          Page {page} of {pageCount} · {files.length.toLocaleString()} shown on this page
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
