"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { getRecommendations } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

const PRIORITY_CLASS: Record<string, string> = {
  critical: "border-red-500/40 text-red-700",
  high: "border-orange-500/40 text-orange-700",
  medium: "border-amber-500/40 text-amber-700",
  low: "border-[var(--border-default)] text-[var(--text-muted)]",
};

export default function V3RecommendationsPage() {
  const { ready, hasToken } = useAccessToken();
  const query = useQuery({
    queryKey: ["recommendations", "current-tenant"],
    queryFn: () => getRecommendations(getTenantId()),
    enabled: ready && hasToken,
    staleTime: 30_000,
  });

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <PageHeader
        title="Recommended actions"
        description="Deterministic suggestions from current CRM deal health and recorded evidence."
        actions={
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void query.refetch()}
              disabled={!hasToken || query.isFetching}
              className="inline-flex items-center gap-2 rounded-md border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-primary)] disabled:opacity-50"
            >
              <RefreshCw className="h-4 w-4" /> {query.isFetching ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        }
      />

      {!ready ? <LoadingState label="Checking session…" /> : !hasToken ? (
        <PermissionState nextPath="/v3/recommendations" />
      ) : query.isLoading ? (
        <LoadingState label="Loading recommendations…" />
      ) : query.isError ? (
        <ErrorState
          title="Could not load recommendations"
          description={query.error instanceof Error ? query.error.message : "Request failed"}
          onRetry={() => void query.refetch()}
        />
      ) : !query.data?.items.length ? (
        <EmptyState
          title="No recommendations to review"
          description={`Checked ${query.data?.source_opportunities ?? 0} open deals. Deals without a recorded probability are skipped instead of scored as if their probability were known.`}
          action={<Link href="/v3/crm" className="text-sm underline">Review CRM deals</Link>}
        />
      ) : (
        <div className="space-y-3" data-testid="recommendation-list">
          {query.data.items.map((item) => (
            <article key={item.id} className="rounded-lg border border-[var(--border-default)] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
                    {item.priority} priority · {Math.round(item.confidence * 100)}% rule confidence
                  </p>
                  <h2 className="mt-1 text-base font-semibold text-[var(--text-primary)]">{item.title}</h2>
                </div>
                <span className={`rounded-full border px-2 py-1 text-xs ${PRIORITY_CLASS[item.priority]}`}>
                  {item.priority}
                </span>
              </div>
              <p className="mt-2 text-sm text-[var(--text-secondary)]">{item.description}</p>
              <p className="mt-2 text-xs text-[var(--text-muted)]">Why: {item.reasoning}</p>
              {item.evidence.length > 0 ? (
                <ul className="mt-3 space-y-1 text-xs text-[var(--text-secondary)]">
                  {item.evidence.map((evidence, index) => (
                    <li key={`${evidence.source_domain}-${index}`}>
                      {evidence.source_domain} · {evidence.description} · {Math.round(evidence.confidence * 100)}%
                    </li>
                  ))}
                </ul>
              ) : null}
              {item.target_type === "opportunity" ? (
                <Link href={`/v3/crm/${encodeURIComponent(item.target_id)}`} className="mt-3 inline-block text-sm underline">
                  Review deal
                </Link>
              ) : null}
            </article>
          ))}
          <p className="text-xs text-[var(--text-muted)]">
            These suggestions do not change CRM records or send communications. Review the linked deal and evidence before taking action.
          </p>
        </div>
      )}
    </div>
  );
}
