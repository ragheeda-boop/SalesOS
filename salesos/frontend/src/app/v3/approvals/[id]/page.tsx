"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@salesos/ui";
import { ArrowLeft, Check, X, ArrowUp } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const statusColors: Record<string, string> = {
  PENDING: "bg-yellow-100 text-yellow-700",
  APPROVED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  ESCALATED: "bg-orange-100 text-orange-700",
  EXPIRED: "bg-gray-200 text-gray-600",
  CANCELLED: "bg-gray-100 text-gray-500",
};

export default function V3ApprovalDetailPage() {
  const { ready, hasToken } = useAccessToken();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const approvalId = params?.id as string;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["approvals", approvalId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/approvals/${approvalId}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && !!approvalId,
  });

  const action = useMutation({
    mutationFn: async (decision: string) => {
      const endpoints: Record<string, string> = {
        approve: "APPROVED",
        reject: "REJECTED",
        escalate: "ESCALATED",
      };
      const decisionValue = endpoints[decision];
      if (!decisionValue) throw new Error(`Unknown decision: ${decision}`);
      await apiClient.post(
        `/api/v1/approvals/${approvalId}/decide`,
        {
          decision: decisionValue,
          decided_by: "current-user",
          authority_level: "MANAGER",
        },
        { headers: { "X-Tenant-Id": getTenantId() } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals", "pending"] });
      queryClient.invalidateQueries({ queryKey: ["approvals", "all"] });
      queryClient.invalidateQueries({ queryKey: ["approvals", "kpis"] });
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath={`/v3/approvals/${approvalId}`} />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const a = data as {
    id?: string;
    status?: string;
    target_type?: string;
    target_id?: string;
    requested_by?: string;
    action_summary?: string;
    action_evidence?: string[];
    required_level?: string;
    assigned_to?: string;
    priority?: number;
    created_at?: string;
    decisions?: Array<{
      decision: string;
      decided_by: string;
      decided_at: string;
      comments?: string;
      authority_level: string;
    }>;
  };
  const status = a?.status ?? "unknown";

  return (
    <>
      <button
        onClick={() => router.push("/v3/approvals")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Approvals
      </button>
      <PageHeader
        title={a?.action_summary || "Approval Request"}
        description={`ID: ${approvalId}`}
      />

      <div className="mb-6 flex items-center gap-3">
        <Badge className={statusColors[status] ?? "bg-gray-100 text-gray-700"}>
          {status}
        </Badge>
        <span className="text-sm text-[var(--text-muted)]">
          {a?.target_type} • Priority {a?.priority ?? 1}
        </span>
        {a?.assigned_to && (
          <span className="text-sm text-[var(--text-muted)]">
            Assigned to: {a.assigned_to}
          </span>
        )}
      </div>

      {/* Evidence */}
      {a?.action_evidence && a.action_evidence.length > 0 && (
        <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Evidence</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--text-muted)]">
            {a.action_evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Decision Timeline */}
      {a?.decisions && a.decisions.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Decision Timeline</h3>
          <div className="space-y-2">
            {a.decisions.map((d, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-[var(--border-default)] p-3 text-sm">
                <Badge className={statusColors[d.decision] ?? "bg-gray-100 text-gray-700"}>
                  {d.decision}
                </Badge>
                <span className="font-medium">{d.decided_by}</span>
                <span className="text-[var(--text-muted)]">{d.authority_level}</span>
                <span className="text-[var(--text-muted)]">
                  {new Date(d.decided_at).toLocaleString()}
                </span>
                {d.comments && (
                  <span className="text-[var(--text-muted)]">— {d.comments}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {status === "PENDING" && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => action.mutate("approve")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
          >
            <Check className="h-4 w-4" /> Approve
          </button>
          <button
            onClick={() => action.mutate("reject")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-danger-border,#fecaca)] px-4 py-2 text-sm text-[var(--status-danger,#991b1b)] hover:bg-[var(--status-danger-bg,#fef2f2)] disabled:opacity-50"
          >
            <X className="h-4 w-4" /> Reject
          </button>
          <button
            onClick={() => action.mutate("escalate")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50"
          >
            <ArrowUp className="h-4 w-4" /> Escalate
          </button>
        </div>
      )}

      {action.isError && (
        <p className="mt-4 text-sm text-[var(--status-danger,#991b1b)]">
          Error: {(action.error as Error)?.message}
        </p>
      )}
    </>
  );
}
