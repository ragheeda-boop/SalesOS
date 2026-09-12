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
import { CreateContractForm } from "./create-contract-form";

type Contract = {
  id: string;
  status: string;
  opportunity_id: string;
  quote_id?: string;
  title: string;
  effective_date?: string;
  expiry_date?: string;
  version: number;
  created_at: string;
};

const statusColors: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  SIGNED: "bg-blue-100 text-blue-700",
  ACTIVE: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-200 text-green-800",
  TERMINATED: "bg-red-100 text-red-700",
  EXPIRED: "bg-gray-200 text-gray-600",
  RENEWED: "bg-purple-100 text-purple-700",
};

export default function V3ContractsPage() {
  const { ready, hasToken } = useAccessToken();
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["contracts", "list"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/contracts", {
        params: {},
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Contract[]; total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/contracts" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const contracts = data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Contracts"
        description="Contract records. Create stays in v3 — POST /api/v1/contracts (opportunity_id required; quote_id and title optional). Sign/activate live on the detail route, not here."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/quotes">Browse quotes</GhostButtonLink>
            {hasToken ? (
              <button
                type="button"
                onClick={() => setShowCreate((open) => !open)}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                data-testid="contracts-new-toggle"
              >
                {showCreate ? "Hide form" : "New contract"}
              </button>
            ) : null}
          </div>
        }
      />
      {showCreate ? <CreateContractForm onCancel={() => setShowCreate(false)} /> : null}
      {contracts.length === 0 ? (
        <EmptyState
          title="No contracts yet"
          description="No contracts in this tenant yet. Create one here — needs opportunity_id. quote_id is optional. Nothing is invented and the list stays empty until POST /api/v1/contracts succeeds."
          action={
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
              data-testid="contracts-empty-create"
            >
              Create contract
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
              <th className="px-4 py-3">Version</th>
              <th className="px-4 py-3">Effective</th>
              <th className="px-4 py-3">Expiry</th>
              <th className="px-4 py-3">Opportunity</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {contracts.map((c) => (
              <tr key={c.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">{c.title || "Untitled"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] ${statusColors[c.status] ?? "bg-gray-100 text-gray-700"}`}
                  >
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">v{c.version}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {c.effective_date ? new Date(c.effective_date).toLocaleDateString() : "-"}
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {c.expiry_date ? new Date(c.expiry_date).toLocaleDateString() : "-"}
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{c.opportunity_id}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/v3/contracts/${c.id}`}
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
