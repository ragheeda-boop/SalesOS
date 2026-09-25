"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@salesos/ui";
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

type Approval = {
  id: string;
  status: string;
  target_type: string;
  target_id: string;
  requested_by: string;
  action_summary: string;
  required_level: string;
  assigned_to?: string;
  priority: number;
  created_at: string;
  decisions: Array<{
    decision: string;
    decided_by: string;
    decided_at: string;
    comments?: string;
  }>;
};

type TabKey = "pending" | "all" | "kpis";

const statusColors: Record<string, string> = {
  PENDING: "bg-yellow-100 text-yellow-700",
  APPROVED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  ESCALATED: "bg-orange-100 text-orange-700",
  EXPIRED: "bg-gray-200 text-gray-600",
  CANCELLED: "bg-gray-100 text-gray-500",
};

export default function V3ApprovalsPage() {
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = React.useState<TabKey>("pending");

  const { data: pendingData, isLoading: pendingLoading, isError: pendingError, error: pendingErr } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/approvals/pending", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Approval[]; total: number };
    },
    enabled: ready && hasToken && tab === "pending",
  });

  const { data: allData, isLoading: allLoading, isError: allError, error: allErr } = useQuery({
    queryKey: ["approvals", "all"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/approvals", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { items: Approval[]; total: number };
    },
    enabled: ready && hasToken && tab === "all",
  });

  const { data: kpis, isLoading: kpisLoading, isError: kpisError, error: kpisErr } = useQuery({
    queryKey: ["approvals", "kpis"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/approvals/kpis", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && tab === "kpis",
  });

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/approvals" />;

  const items = tab === "pending" ? (pendingData?.items ?? []) : (allData?.items ?? []);
  const isLoading = tab === "pending" ? pendingLoading : tab === "all" ? allLoading : kpisLoading;
  const isError = tab === "pending" ? pendingError : tab === "all" ? allError : kpisError;
  const queryError = tab === "pending" ? pendingErr : tab === "all" ? allErr : kpisErr;

  if (isLoading) return <LoadingState label="Loading approvals…" />;
  if (isError)
    return (
      <>
        <PageHeader title="Approvals" description="Review and decide on approval requests" />
        <ErrorState
          title="Could not load approvals"
          description={queryError instanceof Error ? queryError.message : "Request failed"}
        />
      </>
    );

  return (
    <>
      <PageHeader
        title="Approvals"
        description="Review and decide on approval requests"
      />

      {/* Tabs */}
      <div className="mb-4 flex gap-1 rounded-lg border border-[var(--border-default)] p-1">
        {([
          { key: "pending", label: "Pending" },
          { key: "all", label: "All" },
          { key: "kpis", label: "KPIs" },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* KPIs Tab */}
      {tab === "kpis" && kpis && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {[
            { label: "Pending", value: kpis.pending, color: "text-yellow-600" },
            { label: "Approved", value: kpis.approved, color: "text-green-600" },
            { label: "Rejected", value: kpis.rejected, color: "text-red-600" },
            { label: "Escalated", value: kpis.escalated, color: "text-orange-600" },
            { label: "Expired", value: kpis.expired, color: "text-gray-600" },
            { label: "Cancelled", value: kpis.cancelled, color: "text-gray-500" },
          ].map((kpi) => (
            <div key={kpi.label} className="rounded-lg border border-[var(--border-default)] p-4">
              <div className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</div>
              <div className="text-sm text-[var(--text-muted)]">{kpi.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Pending/All Tab */}
      {tab !== "kpis" && (
        <>
          {items.length === 0 ? (
            <EmptyState
              title={tab === "pending" ? "No pending approvals" : "No approvals"}
              description={tab === "pending" ? "All caught up!" : "No approval requests yet."}
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                  <tr>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Requested By</th>
                    <th className="px-4 py-3">Level</th>
                    <th className="px-4 py-3">Decisions</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-default)]">
                  {items.map((a) => (
                    <tr key={a.id} className="hover:bg-[var(--bg-hover)]">
                      <td className="px-4 py-3 max-w-xs truncate font-medium">
                        {a.action_summary || "No summary"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[a.status] ?? "bg-gray-100 text-gray-700"}>
                          {a.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">{a.target_type}</td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">{a.requested_by}</td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">{a.required_level}</td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">{a.decisions?.length ?? 0}</td>
                      <td className="px-4 py-3 text-[var(--text-muted)]">
                        {new Date(a.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          href={`/v3/approvals/${a.id}`}
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
          )}
        </>
      )}
    </>
  );
}
