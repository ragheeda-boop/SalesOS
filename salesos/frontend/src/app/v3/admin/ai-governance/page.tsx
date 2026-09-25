"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listAIGovernanceAudit } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";

function formatDate(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Riyadh",
  }).format(parsed);
}

export default function AIGovernanceAuditPage() {
  const { ready, hasToken } = useAccessToken();
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["ai-governance-audit", getTenantId(), page],
    queryFn: () => listAIGovernanceAudit(getTenantId(), { page, page_size: 25 }),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <PageHeader
        title="AI Governance Audit"
        description="Tenant-scoped policy enforcement, human approval, and PII guardrail events. Read-only."
      />
      {!ready ? <LoadingState label="Checking session…" /> : !hasToken ? (
        <PermissionState nextPath="/v3/admin/ai-governance" />
      ) : query.isLoading ? (
        <LoadingState label="Loading governance events…" />
      ) : query.isError ? (
        <ErrorState
          title="Could not load governance events"
          description={query.error instanceof Error ? query.error.message : "Request failed"}
          onRetry={() => void query.refetch()}
        />
      ) : !query.data?.items.length ? (
        <EmptyState
          title="No AI governance events"
          description="No persisted policy, approval, or PII guardrail audit events were returned for this tenant."
        />
      ) : (
        <>
          <p className="text-xs text-[var(--text-muted)]" aria-live="polite">
            {query.data.total} events · showing page {query.data.page} · records are read-only
          </p>
          <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-xs text-[var(--text-muted)]">
                  <tr>
                    <th scope="col" className="px-3 py-2.5 font-medium">Event</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Policy / decision</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Actor</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Outcome</th>
                    <th scope="col" className="px-3 py-2.5 font-medium">Recorded</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.items.map((event) => (
                    <tr key={event.id} className="border-b border-[var(--border-default)] last:border-0">
                      <td className="px-3 py-2.5">
                        <span className="block font-medium text-[var(--text-primary)]">
                          {event.action.replace(/[:_]/g, " ")}
                        </span>
                        <span className="text-xs text-[var(--text-muted)]">{event.resource_type}</span>
                      </td>
                      <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                        {event.policy_name || event.decision || event.enforcement_action || "—"}
                      </td>
                      <td className="px-3 py-2.5 text-[var(--text-secondary)]">{event.user_id || "System"}</td>
                      <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">{event.outcome}</td>
                      <td className="px-3 py-2.5 text-[var(--text-secondary)]">{formatDate(event.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <button
              type="button"
              disabled={page <= 1 || query.isFetching}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              className="rounded-md border border-[var(--border-default)] px-3 py-2 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-xs text-[var(--text-muted)]">
              Page {page} of {Math.max(1, Math.ceil(query.data.total / query.data.page_size))}
            </span>
            <button
              type="button"
              disabled={page * query.data.page_size >= query.data.total || query.isFetching}
              onClick={() => setPage((current) => current + 1)}
              className="rounded-md border border-[var(--border-default)] px-3 py-2 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            Sensitive comments and raw payloads are omitted. Access requires the tenant audit read permission.
          </p>
        </>
      )}
    </div>
  );
}
