"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@salesos/ui";
import { ArrowLeft, Check, X, AlertTriangle, UserPlus } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  in_progress: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  escalated: "bg-orange-100 text-orange-700",
  cancelled: "bg-gray-200 text-gray-600",
};

export default function V3ReviewDetailPage() {
  const { ready, hasToken } = useAccessToken();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const reviewId = params?.id as string;
  const [assignTo, setAssignTo] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["reviews", reviewId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/reviews/${reviewId}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && !!reviewId,
  });

  const decide = useMutation({
    mutationFn: async (decision: string) => {
      await apiClient.post(
        `/api/v1/reviews/${reviewId}/decide?decision=${decision}&decided_by=manager&comments=`,
        {},
        { headers: { "X-Tenant-Id": getTenantId() } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", reviewId] });
      queryClient.invalidateQueries({ queryKey: ["reviews", "list"] });
    },
  });

  const assign = useMutation({
    mutationFn: async () => {
      await apiClient.post(
        `/api/v1/reviews/${reviewId}/assign?assigned_to=${assignTo}`,
        {},
        { headers: { "X-Tenant-Id": getTenantId() } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", reviewId] });
      setAssignTo("");
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath={`/v3/reviews/${reviewId}`} />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const r = data as { id?: string; status?: string; review_type?: string; target_type?: string; target_id?: string; assigned_to?: string; decision_count?: number };
  const status = r?.status ?? "unknown";
  const isTerminal = ["approved", "rejected", "cancelled"].includes(status);

  return (
    <>
      <button
        onClick={() => router.push("/v3/reviews")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Reviews
      </button>
      <PageHeader
        title={`${r?.review_type?.replace(/_/g, " ") ?? "Review"}`}
        description={`ID: ${reviewId}`}
      />

      <div className="mb-6 grid grid-cols-2 gap-4 text-sm">
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <p className="text-xs uppercase text-[var(--text-muted)]">Status</p>
          <Badge className={statusColors[status] ?? "bg-gray-100 text-gray-700"}>
            {status.replace(/_/g, " ")}
          </Badge>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <p className="text-xs uppercase text-[var(--text-muted)]">Target</p>
          <p className="font-medium">{r?.target_type}: {r?.target_id}</p>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <p className="text-xs uppercase text-[var(--text-muted)]">Assigned To</p>
          <p className="font-medium">{r?.assigned_to || "Unassigned"}</p>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <p className="text-xs uppercase text-[var(--text-muted)]">Decisions</p>
          <p className="font-medium">{r?.decision_count ?? 0}</p>
        </div>
      </div>

      {!isTerminal && (
        <div className="space-y-4">
          {status === "pending" && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={assignTo}
                onChange={(e) => setAssignTo(e.target.value)}
                placeholder="Assign to user ID..."
                className="rounded-md border border-[var(--border-default)] px-3 py-1.5 text-sm"
              />
              <button
                onClick={() => assign.mutate()}
                disabled={!assignTo || assign.isPending}
                className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50"
              >
                <UserPlus className="h-4 w-4" /> Assign
              </button>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => decide.mutate("approve")}
              disabled={decide.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
            >
              <Check className="h-4 w-4" /> Approve
            </button>
            <button
              onClick={() => decide.mutate("reject")}
              disabled={decide.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-danger-border,#fecaca)] px-4 py-2 text-sm text-[var(--status-danger,#991b1b)] hover:hover:bg-[var(--status-danger-bg,#fef2f2)] disabled:opacity-50"
            >
              <X className="h-4 w-4" /> Reject
            </button>
            <button
              onClick={() => decide.mutate("escalate")}
              disabled={decide.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-warning-border,#fed7aa)] px-4 py-2 text-sm text-[var(--status-warning,#9a3412)] hover:hover:bg-[var(--status-warning-bg,#fff7ed)] disabled:opacity-50"
            >
              <AlertTriangle className="h-4 w-4" /> Escalate
            </button>
          </div>
        </div>
      )}

      {(decide.isError || assign.isError) && (
        <p className="mt-4 text-sm text-[var(--status-danger,#991b1b)]">
          Error: {((decide.error || assign.error) as Error)?.message}
        </p>
      )}
    </>
  );
}
