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

type Review = {
  id: string;
  status: string;
  review_type: string;
  target_id: string;
  target_type: string;
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  in_progress: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  escalated: "bg-orange-100 text-orange-700",
  cancelled: "bg-gray-200 text-gray-600",
};

export default function V3ReviewsPage() {
  const { ready, hasToken } = useAccessToken();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["reviews", "list"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/reviews", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Review[]; total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/reviews" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const reviews = data?.items ?? [];

  if (reviews.length === 0)
    return (
      <>
        <PageHeader
          title="Reviews"
          description="Manager, deal, and exception review workflows"
        />
        <EmptyState
          title="No reviews yet"
          description="Create a review for a deal, quote, or proposal to start the approval workflow."
        />
      </>
    );

  return (
    <>
      <PageHeader
        title="Reviews"
        description="Manager, deal, and exception review workflows"
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
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {reviews.map((r) => (
              <tr key={r.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">{r.review_type.replace(/_/g, " ")}</td>
                <td className="px-4 py-3">
                  <Badge className={statusColors[r.status] ?? "bg-gray-100 text-gray-700"}>
                    {r.status.replace(/_/g, " ")}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {r.target_type}: {r.target_id}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/v3/reviews/${r.id}`}
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
