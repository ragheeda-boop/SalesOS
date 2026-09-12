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
import { CreateQuoteForm } from "./create-quote-form";

type Quote = {
  id: string;
  status: string;
  opportunity_id: string;
  title: string;
  version: number;
  grand_total: number;
  currency: string;
  created_at: string;
};

const statusColors: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  APPROVED: "bg-green-100 text-green-700",
  SENT: "bg-purple-100 text-purple-700",
  ACCEPTED: "bg-green-200 text-green-800",
  REJECTED: "bg-red-100 text-red-700",
  EXPIRED: "bg-gray-200 text-gray-600",
  REVISED: "bg-yellow-100 text-yellow-700",
};

function formatCurrency(amount: number, currency: string = "SAR") {
  return new Intl.NumberFormat("en-SA", { style: "currency", currency }).format(amount);
}

export default function V3QuotesPage() {
  const { ready, hasToken } = useAccessToken();
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["quotes", "list"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/quotes", {
        params: {},
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Quote[]; total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath="/v3/quotes" />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const quotes = data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Quotes"
        description="Quote lifecycle — draft, submit, approve, send, accept. Create stays in v3 — POST /api/v1/quotes (query opportunity_id + title)."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/crm">Browse deals</GhostButtonLink>
            {hasToken ? (
              <button
                type="button"
                onClick={() => setShowCreate((open) => !open)}
                className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                data-testid="quotes-new-toggle"
              >
                {showCreate ? "Hide form" : "New quote"}
              </button>
            ) : null}
          </div>
        }
      />
      {showCreate ? <CreateQuoteForm onCancel={() => setShowCreate(false)} /> : null}
      {quotes.length === 0 ? (
        <EmptyState
          title="No quotes yet"
          description="No quotes in this tenant yet. Create one here — nothing is invented and the list stays empty until POST /api/v1/quotes succeeds."
          action={
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
              data-testid="quotes-empty-create"
            >
              Create quote
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
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Opportunity</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]">
            {quotes.map((q) => (
              <tr key={q.id} className="hover:bg-[var(--bg-hover)]">
                <td className="px-4 py-3 font-medium">{q.title || "Untitled"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] ${statusColors[q.status] ?? "bg-gray-100 text-gray-700"}`}
                  >
                    {q.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">v{q.version}</td>
                <td className="px-4 py-3 font-medium">
                  {formatCurrency(q.grand_total, q.currency)}
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{q.opportunity_id}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {new Date(q.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/v3/quotes/${q.id}`}
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
