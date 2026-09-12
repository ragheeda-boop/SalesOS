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
import { CreateProposalForm } from "./create-proposal-form";

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
  const [showCreate, setShowCreate] = useState(false);

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

  return (
    <>
      <PageHeader
        title="Proposals"
        description="Proposal lifecycle — draft, approve, deliver, accept. Create stays in v3 — POST /api/v1/proposals (query opportunity_id + quote_id)."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/quotes">Browse quotes</GhostButtonLink>
            {hasToken ? (
              <button
                type="button"
                onClick={() => setShowCreate((open) => !open)}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                data-testid="proposals-new-toggle"
              >
                {showCreate ? "Hide form" : "New proposal"}
              </button>
            ) : null}
          </div>
        }
      />
      {showCreate ? <CreateProposalForm onCancel={() => setShowCreate(false)} /> : null}
      {proposals.length === 0 ? (
        <EmptyState
          title="No proposals yet"
          description="No proposals in this tenant yet. Create one here — needs a quote first. Nothing is invented and the list stays empty until POST /api/v1/proposals succeeds."
          action={
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
              data-testid="proposals-empty-create"
            >
              Create proposal
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
                      <span
                        className={`rounded-full px-2 py-0.5 text-[11px] ${statusColors[p.status] ?? "bg-gray-100 text-gray-700"}`}
                      >
                        {p.status}
                      </span>
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
      )}
    </>
  );
}
