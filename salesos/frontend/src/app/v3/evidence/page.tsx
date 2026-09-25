"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { listCommercialEvidence } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

const CATEGORIES = [
  "account_health",
  "deal_risk",
  "deal_opportunity",
  "pipeline_velocity",
  "revenue_forecast",
  "engagement_trend",
  "churn_risk",
  "expansion_potential",
  "activity_anomaly",
  "cross_sell",
];

function formatWhen(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Riyadh",
  }).format(date);
}

export default function EvidencePage() {
  const { ready, hasToken } = useAccessToken();
  const [page, setPage] = useState(1);
  const [draftTargetType, setDraftTargetType] = useState("");
  const [draftTargetId, setDraftTargetId] = useState("");
  const [draftCategory, setDraftCategory] = useState("");
  const [filters, setFilters] = useState({ target_type: "", target_id: "", category: "" });

  const query = useQuery({
    queryKey: ["commercial-evidence", getTenantId(), page, filters],
    queryFn: () =>
      listCommercialEvidence(getTenantId(), {
        page,
        page_size: 20,
        ...(filters.target_type ? { target_type: filters.target_type } : {}),
        ...(filters.target_id ? { target_id: filters.target_id } : {}),
        ...(filters.category ? { category: filters.category } : {}),
      }),
    enabled: ready && hasToken,
  });

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setFilters({
      target_type: draftTargetType.trim(),
      target_id: draftTargetId.trim(),
      category: draftCategory,
    });
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <PageHeader
        title="Evidence chain"
        description="Review persisted commercial insights alongside their recorded sources, timestamps, and confidence. Read-only."
      />
      {!ready ? <LoadingState label="Checking session…" /> : !hasToken ? (
        <PermissionState nextPath="/v3/evidence" />
      ) : (
        <>
          <form
            onSubmit={applyFilters}
            className="grid gap-3 rounded-lg border border-[var(--border-default)] p-3 sm:grid-cols-4"
          >
            <label className="space-y-1 text-xs text-[var(--text-secondary)]">
              <span>Insight category</span>
              <select
                aria-label="Insight category"
                value={draftCategory}
                onChange={(event) => setDraftCategory(event.target.value)}
                className="w-full rounded border border-[var(--border-default)] px-2 py-2 text-sm"
              >
                <option value="">All categories</option>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>{category.replace(/_/g, " ")}</option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-xs text-[var(--text-secondary)]">
              <span>Target type</span>
              <select
                aria-label="Target type"
                value={draftTargetType}
                onChange={(event) => setDraftTargetType(event.target.value)}
                className="w-full rounded border border-[var(--border-default)] px-2 py-2 text-sm"
              >
                <option value="">All targets</option>
                <option value="company">Company</option>
                <option value="opportunity">Opportunity</option>
                <option value="contact">Contact</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-[var(--text-secondary)]">
              <span>Target ID</span>
              <input
                aria-label="Target ID"
                value={draftTargetId}
                onChange={(event) => setDraftTargetId(event.target.value)}
                maxLength={64}
                className="w-full rounded border border-[var(--border-default)] px-2 py-2 text-sm"
              />
            </label>
            <button
              type="submit"
              disabled={query.isFetching}
              className="self-end rounded-md border border-[var(--border-default)] px-3 py-2 text-sm disabled:opacity-50"
            >
              Apply filters
            </button>
          </form>

          {query.isLoading ? <LoadingState label="Loading evidence chains…" /> : query.isError ? (
            <ErrorState
              title="Could not load evidence chains"
              description={query.error instanceof Error ? query.error.message : "Request failed"}
              onRetry={() => void query.refetch()}
            />
          ) : !query.data?.items.length ? (
            <EmptyState
              title="No persisted insights"
              description="No commercial insight rows matched this tenant and filter. An empty result is not evidence that an insight exists."
            />
          ) : (
            <>
              <p className="text-xs text-[var(--text-muted)]" aria-live="polite">
                {query.data.total} insights · page {query.data.page} · source payloads are omitted
              </p>
              <div className="space-y-3">
                {query.data.items.map((insight) => (
                  <article key={insight.id} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                          {insight.category.replace(/_/g, " ")} · {insight.target_type}
                        </p>
                        <h2 className="mt-1 text-base font-semibold text-[var(--text-primary)]">{insight.title}</h2>
                      </div>
                      <span className="rounded-full border border-[var(--border-default)] px-2.5 py-1 text-xs capitalize text-[var(--text-secondary)]">
                        {insight.confidence_level} · {Math.round(insight.overall_confidence * 100)}%
                      </span>
                    </div>
                    {insight.description ? (
                      <p className="mt-2 text-sm text-[var(--text-secondary)]">{insight.description}</p>
                    ) : null}
                    <p className="mt-2 text-xs text-[var(--text-muted)]">
                      Target {insight.target_id} · recorded {formatWhen(insight.created_at)}
                      {insight.target_type === "company" ? (
                        <> · <Link href={`/v3/companies/${encodeURIComponent(insight.target_id)}`} className="underline">Open company</Link></>
                      ) : insight.target_type === "opportunity" ? (
                        <> · <Link href={`/v3/crm/${encodeURIComponent(insight.target_id)}`} className="underline">Open deal</Link></>
                      ) : null}
                    </p>
                    <div className="mt-3 border-t border-[var(--border-default)] pt-3">
                      <h3 className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
                        Evidence ({insight.evidence_items.length})
                      </h3>
                      {insight.evidence_items.length ? (
                        <ul className="mt-2 space-y-2">
                          {insight.evidence_items.map((evidence) => (
                            <li key={evidence.id} className="rounded-md bg-[var(--bg-secondary)] p-3">
                              <p className="text-sm text-[var(--text-primary)]">{evidence.description}</p>
                              <p className="mt-1 text-xs text-[var(--text-secondary)]">
                                {evidence.source_domain} · {evidence.source_type}
                                {evidence.source_name ? ` · ${evidence.source_name}` : ""}
                                {evidence.source_id ? ` · ${evidence.source_id}` : ""}
                              </p>
                              <p className="mt-1 text-xs text-[var(--text-muted)]">
                                {evidence.evidence_kind || "Unclassified legacy evidence"} · {evidence.confidence_level} · {Math.round(evidence.confidence * 100)}% · {formatWhen(evidence.recorded_at)}
                              </p>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-2 text-sm text-[var(--text-muted)]">No evidence items are linked to this insight.</p>
                      )}
                    </div>
                  </article>
                ))}
              </div>
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  disabled={page <= 1 || query.isFetching}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  className="rounded-md border border-[var(--border-default)] px-3 py-2 text-sm disabled:opacity-50"
                >Previous</button>
                <span className="text-xs text-[var(--text-muted)]">
                  Page {page} of {Math.max(1, Math.ceil(query.data.total / query.data.page_size))}
                </span>
                <button
                  type="button"
                  disabled={page * query.data.page_size >= query.data.total || query.isFetching}
                  onClick={() => setPage((current) => current + 1)}
                  className="rounded-md border border-[var(--border-default)] px-3 py-2 text-sm disabled:opacity-50"
                >Next</button>
              </div>
            </>
          )}
          <p className="text-xs text-[var(--text-muted)]">
            This view does not recalculate confidence or apply evidence to company, contact, or deal records.
          </p>
        </>
      )}
    </div>
  );
}
