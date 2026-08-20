"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@salesos/ui";
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

type Proposal = {
  id: string;
  status: string;
  opportunity_id: string;
  title: string;
};

const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  generated: "bg-blue-100 text-blue-700",
  reviewed: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  delivered: "bg-purple-100 text-purple-700",
  viewed: "bg-indigo-100 text-indigo-700",
  accepted: "bg-green-200 text-green-800",
  rejected: "bg-red-100 text-red-700",
  expired: "bg-gray-200 text-gray-600",
};

export default function V3ProposalsPage() {
  const { ready, hasToken } = useAccessToken();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["proposals", "list"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/proposals", {
        params: {},
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Proposal[]; total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/proposals" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const proposals = data?.items ?? [];

  if (proposals.length === 0)
    return (
      <>
        <PageHeader
          title="Proposals"
          description="Manage proposal lifecycle — draft, approve, deliver, accept"
        />
        <EmptyState
          title="No proposals yet"
          description="Create a proposal from an opportunity and quote."
        />
      </>
    );

  return (
    <>
      <PageHeader
        title="Proposals"
        description="Manage proposal lifecycle — draft, approve, deliver, accept"
      />
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
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Opportunity</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {proposals.map((p) => (
              <tr key={p.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">{p.title || "Untitled"}</td>
                <td className="px-4 py-3">
                  <Badge className={statusColors[p.status] ?? "bg-gray-100 text-gray-700"}>
                    {p.status}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{p.opportunity_id}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/v3/proposals/${p.id}`}
                    className="text-[var(--text-link,theme(colors.blue.600))] hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
