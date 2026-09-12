"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";
import { CreateReviewForm } from "./create-review-form";

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
  const [showCreate, setShowCreate] = useState(false);

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

  return (
    <>
      <PageHeader
        title="Reviews"
        description="Manager, deal, and exception reviews. Create stays in v3 — POST /api/v1/reviews (query review_type + target_id + target_type)."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/crm">Browse deals</GhostButtonLink>
            {hasToken ? (
              <button
                type="button"
                onClick={() => setShowCreate((open) => !open)}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                data-testid="reviews-new-toggle"
              >
                {showCreate ? "Hide form" : "New review"}
              </button>
            ) : null}
          </div>
        }
      />
      {showCreate ? <CreateReviewForm onCancel={() => setShowCreate(false)} /> : null}
      {reviews.length === 0 ? (
        <EmptyState
          title="No reviews yet"
          description="No reviews in this tenant yet. Create one here — needs a deal, quote, or proposal as target_id. Nothing is invented and the list stays empty until POST /api/v1/reviews succeeds."
          action={
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
              data-testid="reviews-empty-create"
            >
              Create review
            </button>
          }
        />
      ) : (
        <>
          <div className="mb-4 flex gap-2">
            <button
              onClick={() => refetch()}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
            >
              Refresh
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
                      <span
                        className={`rounded-full px-2 py-0.5 text-[11px] ${statusColors[r.status] ?? "bg-gray-100 text-gray-700"}`}
                      >
                        {r.status.replace(/_/g, " ")}
                      </span>
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
      )}
    </>
  );
}
