"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@salesos/ui";
import { ArrowLeft, Check, X, Send, RotateCcw } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

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

export default function V3QuoteDetailPage() {
  const { ready, hasToken } = useAccessToken();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const quoteId = params?.id as string;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["quotes", quoteId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/quotes/${quoteId}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && !!quoteId,
  });

  const action = useMutation({
    mutationFn: async (action: string) => {
      const endpoints: Record<string, { method: string; url: string; body?: unknown }> = {
        submit: { method: "post", url: `/api/v1/quotes/${quoteId}/submit` },
        approve: {
          method: "post",
          url: `/api/v1/quotes/${quoteId}/approve`,
          body: { approved_by: "manager", approval_level: "MANAGER" },
        },
        send: { method: "post", url: `/api/v1/quotes/${quoteId}/send` },
        accept: { method: "post", url: `/api/v1/quotes/${quoteId}/accept` },
        reject: {
          method: "post",
          url: `/api/v1/quotes/${quoteId}/reject`,
          body: { reason: "declined" },
        },
        revise: { method: "post", url: `/api/v1/quotes/${quoteId}/revise` },
      };
      const ep = endpoints[action];
      if (!ep) throw new Error(`Unknown action: ${action}`);
      await apiClient.post(ep.url, ep.body ?? undefined, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quotes", quoteId] });
      queryClient.invalidateQueries({ queryKey: ["quotes", "list"] });
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath={`/v3/quotes/${quoteId}`} />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const q = data as {
    id?: string;
    status?: string;
    title?: string;
    version?: number;
    grand_total?: number;
    total_tax?: number;
    total_discount?: number;
    subtotal?: number;
    currency?: string;
    opportunity_id?: string;
    lines?: Array<{
      id: string;
      description: string;
      quantity: number;
      unit_price: number;
      discount_percent: number;
      tax_percent: number;
      line_total: number;
      grand_total: number;
    }>;
    approval?: {
      level?: string;
      approved_by?: string;
      approved_at?: string;
      comments?: string;
    };
    revisions?: Array<{
      version: number;
      status: string;
      grand_total: number;
      created_at: string;
    }>;
  };
  const status = q?.status ?? "unknown";

  return (
    <>
      <button
        onClick={() => router.push("/v3/quotes")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Quotes
      </button>
      <PageHeader
        title={q?.title || "Quote"}
        description={`ID: ${quoteId} • Version ${q?.version ?? 1}`}
      />

      <div className="mb-6 flex items-center gap-3">
        <Badge className={statusColors[status] ?? "bg-gray-100 text-gray-700"}>
          {status}
        </Badge>
        <span className="text-sm text-[var(--text-muted)]">
          {q?.opportunity_id}
        </span>
      </div>

      {/* Line Items */}
      {q?.lines && q.lines.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Line Items</h3>
          <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Qty</th>
                  <th className="px-4 py-3">Unit Price</th>
                  <th className="px-4 py-3">Discount</th>
                  <th className="px-4 py-3">Tax</th>
                  <th className="px-4 py-3">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {q.lines.map((line) => (
                  <tr key={line.id} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3">{line.description}</td>
                    <td className="px-4 py-3">{line.quantity}</td>
                    <td className="px-4 py-3">{formatCurrency(line.unit_price, q?.currency)}</td>
                    <td className="px-4 py-3">{line.discount_percent}%</td>
                    <td className="px-4 py-3">{line.tax_percent}%</td>
                    <td className="px-4 py-3 font-medium">
                      {formatCurrency(line.grand_total, q?.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-[var(--bg-secondary)]">
                <tr>
                  <td colSpan={5} className="px-4 py-3 text-right font-medium">Subtotal</td>
                  <td className="px-4 py-3 font-medium">{formatCurrency(q?.subtotal ?? 0, q?.currency)}</td>
                </tr>
                <tr>
                  <td colSpan={5} className="px-4 py-3 text-right text-[var(--text-muted)]">Discount</td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">-{formatCurrency(q?.total_discount ?? 0, q?.currency)}</td>
                </tr>
                <tr>
                  <td colSpan={5} className="px-4 py-3 text-right text-[var(--text-muted)]">Tax</td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">+{formatCurrency(q?.total_tax ?? 0, q?.currency)}</td>
                </tr>
                <tr>
                  <td colSpan={5} className="px-4 py-3 text-right font-bold">Grand Total</td>
                  <td className="px-4 py-3 font-bold">{formatCurrency(q?.grand_total ?? 0, q?.currency)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Approval State */}
      {q?.approval && q.approval.level && (
        <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Approval</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-[var(--text-muted)]">Level:</span> {q.approval.level}</div>
            <div><span className="text-[var(--text-muted)]">Approved by:</span> {q.approval.approved_by}</div>
            <div><span className="text-[var(--text-muted)]">Date:</span> {q.approval.approved_at ? new Date(q.approval.approved_at).toLocaleString() : "-"}</div>
            {q.approval.comments && <div><span className="text-[var(--text-muted)]">Comments:</span> {q.approval.comments}</div>}
          </div>
        </div>
      )}

      {/* Revision History */}
      {q?.revisions && q.revisions.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Revision History</h3>
          <div className="space-y-2">
            {q.revisions.map((rev) => (
              <div key={rev.version} className="flex items-center gap-3 rounded-lg border border-[var(--border-default)] p-3 text-sm">
                <Badge className="bg-[var(--bg-secondary)] text-[var(--text-muted)]">v{rev.version}</Badge>
                <Badge className={statusColors[rev.status] ?? "bg-gray-100 text-gray-700"}>
                  {rev.status}
                </Badge>
                <span className="text-[var(--text-muted)]">
                  {formatCurrency(rev.grand_total, q?.currency)}
                </span>
                <span className="text-[var(--text-muted)]">
                  {new Date(rev.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {status === "DRAFT" && (
          <button
            onClick={() => action.mutate("submit")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-info,#3b82f6)] px-4 py-2 text-sm text-white hover:bg-[var(--status-info-hover,#2563eb)] disabled:opacity-50"
          >
            <Send className="h-4 w-4" /> Submit
          </button>
        )}
        {status === "SUBMITTED" && (
          <>
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
          </>
        )}
        {status === "APPROVED" && (
          <button
            onClick={() => action.mutate("send")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-info,#7c3aed)] px-4 py-2 text-sm text-white hover:bg-[var(--status-info-hover,#6d28d9)] disabled:opacity-50"
          >
            <Send className="h-4 w-4" /> Send
          </button>
        )}
        {status === "SENT" && (
          <>
            <button
              onClick={() => action.mutate("accept")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
            >
              <Check className="h-4 w-4" /> Accept
            </button>
            <button
              onClick={() => action.mutate("reject")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-danger-border,#fecaca)] px-4 py-2 text-sm text-[var(--status-danger,#991b1b)] hover:bg-[var(--status-danger-bg,#fef2f2)] disabled:opacity-50"
            >
              <X className="h-4 w-4" /> Reject
            </button>
          </>
        )}
        {["REJECTED", "EXPIRED"].includes(status) && (
          <button
            onClick={() => action.mutate("revise")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" /> Revise
          </button>
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
