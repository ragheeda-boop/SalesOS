"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@salesos/ui";
import { ArrowLeft, Check, X, Clock, Send } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  approved: "bg-green-100 text-green-700",
  delivered: "bg-purple-100 text-purple-700",
  viewed: "bg-indigo-100 text-indigo-700",
  accepted: "bg-green-200 text-green-800",
  rejected: "bg-red-100 text-red-700",
  expired: "bg-gray-200 text-gray-600",
};

export default function V3ProposalDetailPage() {
  const { ready, hasToken } = useAccessToken();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const proposalId = params?.id as string;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["proposals", proposalId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/proposals/${proposalId}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && !!proposalId,
  });

  const action = useMutation({
    mutationFn: async (action: string) => {
      const endpoints: Record<string, string> = {
        approve: `/api/v1/proposals/${proposalId}/approve?approved_by=manager`,
        deliver: `/api/v1/proposals/${proposalId}/deliver?method=email`,
        accept: `/api/v1/proposals/${proposalId}/accept`,
        reject: `/api/v1/proposals/${proposalId}/reject?reason=declined`,
        expire: `/api/v1/proposals/${proposalId}/expire`,
      };
      const url = endpoints[action];
      if (!url) throw new Error(`Unknown action: ${action}`);
      await apiClient.post(url, {}, { headers: { "X-Tenant-Id": getTenantId() } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proposals", proposalId] });
      queryClient.invalidateQueries({ queryKey: ["proposals", "list"] });
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath={`/v3/proposals/${proposalId}`} />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const p = data as { id?: string; status?: string; title?: string; sections?: number; delivery_method?: string };
  const status = p?.status ?? "unknown";

  return (
    <>
      <button
        onClick={() => router.push("/v3/proposals")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Proposals
      </button>
      <PageHeader title={p?.title || "Proposal"} description={`ID: ${proposalId}`} />

      <div className="mb-6 flex items-center gap-3">
        <Badge className={statusColors[status] ?? "bg-gray-100 text-gray-700"}>
          {status}
        </Badge>
        <span className="text-sm text-[var(--text-muted)]">
          {p?.sections ?? 0} sections • {p?.delivery_method ?? "email"}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {status === "draft" && (
          <button
            onClick={() => action.mutate("approve")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
          >
            <Check className="h-4 w-4" /> Approve
          </button>
        )}
        {status === "approved" && (
          <button
            onClick={() => action.mutate("deliver")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-info,#7c3aed)] px-4 py-2 text-sm text-white hover:hover:bg-[var(--status-info-hover,#6d28d9)] disabled:opacity-50"
          >
            <Send className="h-4 w-4" /> Deliver
          </button>
        )}
        {(status === "delivered" || status === "viewed") && (
          <button
            onClick={() => action.mutate("accept")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
          >
            <Check className="h-4 w-4" /> Accept
          </button>
        )}
        {!["accepted", "rejected", "expired"].includes(status) && (
          <>
            <button
              onClick={() => action.mutate("reject")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-danger-border,#fecaca)] px-4 py-2 text-sm text-[var(--status-danger,#991b1b)] hover:hover:bg-[var(--status-danger-bg,#fef2f2)] disabled:opacity-50"
            >
              <X className="h-4 w-4" /> Reject
            </button>
            <button
              onClick={() => action.mutate("expire")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50"
            >
              <Clock className="h-4 w-4" /> Expire
            </button>
          </>
        )}
      </div>

      {action.isError && (
        <p className="mt-4 text-sm text-[var(--status-danger,#991b1b)]">
          Error: {(action.error as Error)?.message}
        </p>
      )}
    </>
  );
}
