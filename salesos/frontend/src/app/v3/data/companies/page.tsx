"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

type Company = {
  id: string;
  slug: string;
  canonical_name: string;
  canonical_name_ar: string | null;
  cr_number: string | null;
  cr_number_kind?: string | null;
  vat_number: string | null;
  unified_national_number: string | null;
  status: string;
  created_at: string;
};

const REGISTRY_KIND_LABELS: Record<string, string> = {
  UNIFIED_NATIONAL_NUMBER: "Unified national number",
  COMMERCIAL_REGISTRATION: "Commercial registration",
};

export default function V3DataCompaniesPage() {
  const { ready, hasToken } = useAccessToken();
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["masterData", "companies", page],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-companies", {
        params: { page, page_size: pageSize },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as {
        items: Company[];
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
      };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/data/companies" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const companies = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  if (companies.length === 0)
    return (
      <>
        <PageHeader
          title="Global Companies"
          description={`${total.toLocaleString()} canonical records`}
        />
        <EmptyState
          title="No companies found"
          description="There are no canonical company records to display."
        />
      </>
    );

  return (
    <>
      <PageHeader title="Global Companies" description={`${total.toLocaleString()} records`} />
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
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Global ID</th>
              <th className="px-4 py-3">Registry number</th>
              <th className="px-4 py-3">VAT number</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {companies.map((c) => (
              <tr key={c.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">
                  <div>{c.canonical_name}</div>
                  {c.canonical_name_ar ? (
                    <div className="mt-1 text-xs font-normal text-[var(--text-muted)]" dir="rtl">
                      {c.canonical_name_ar}
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{c.id}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  <div>{c.cr_number || "-"}</div>
                  {c.cr_number_kind && c.cr_number_kind !== "UNKNOWN" ? (
                    <div className="mt-1 text-xs">
                      {REGISTRY_KIND_LABELS[c.cr_number_kind] ?? c.cr_number_kind}
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{c.vat_number || "-"}</td>
                <td className="px-4 py-3">{c.status || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3 text-sm">
        <span className="text-[var(--text-muted)]">
          Page {page} of {pageCount} · {companies.length.toLocaleString()} shown on this page
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
