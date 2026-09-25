"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@salesos/ui";
import { ArrowLeft, Check, X, RotateCcw, FileSignature } from "lucide-react";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const statusColors: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  SIGNED: "bg-blue-100 text-blue-700",
  ACTIVE: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-200 text-green-800",
  TERMINATED: "bg-red-100 text-red-700",
  EXPIRED: "bg-gray-200 text-gray-600",
  RENEWED: "bg-purple-100 text-purple-700",
};

export default function V3ContractDetailPage() {
  const { ready, hasToken } = useAccessToken();
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const contractId = params?.id as string;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["contracts", contractId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/contracts/${contractId}`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data;
    },
    enabled: ready && hasToken && !!contractId,
  });

  const action = useMutation({
    mutationFn: async (action: string) => {
      const endpoints: Record<string, { method: string; url: string; body?: unknown }> = {
        sign: {
          method: "post",
          url: `/api/v1/contracts/${contractId}/sign`,
          body: { signed_by: "current-user", signed_by_name: "Current User" },
        },
        complete: { method: "post", url: `/api/v1/contracts/${contractId}/complete` },
        terminate: {
          method: "post",
          url: `/api/v1/contracts/${contractId}/terminate`,
          body: { reason: "terminated" },
        },
        renew: { method: "post", url: `/api/v1/contracts/${contractId}/renew` },
      };
      const ep = endpoints[action];
      if (!ep) throw new Error(`Unknown action: ${action}`);
      await apiClient.post(ep.url, ep.body ?? undefined, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts", contractId] });
      queryClient.invalidateQueries({ queryKey: ["contracts", "list"] });
    },
  });

  if (!ready) return <LoadingState />;
  if (!hasToken) return <PermissionState nextPath={`/v3/contracts/${contractId}`} />;
  if (isLoading) return <LoadingState />;
  if (isError)
    return <ErrorState description={(error as Error)?.message} onRetry={() => refetch()} />;

  const c = data as {
    id?: string;
    status?: string;
    title?: string;
    version?: number;
    opportunity_id?: string;
    quote_id?: string;
    effective_date?: string;
    expiry_date?: string;
    parties?: Array<{ name: string; role: string; contact_email?: string; signatory_name?: string }>;
    obligations?: Array<{ description: string; owner?: string; due_date?: string; status: string }>;
    renewal?: { auto_renew: boolean; notice_days: number; renewal_term_months: number; max_renewals: number };
    legal_terms?: string;
    governing_law?: string;
    signed_by_provider?: string;
    signed_by_customer?: string;
  };
  const status = c?.status ?? "unknown";

  return (
    <>
      <button
        onClick={() => router.push("/v3/contracts")}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Contracts
      </button>
      <PageHeader
        title={c?.title || "Contract"}
        description={`ID: ${contractId} • Version ${c?.version ?? 1}`}
      />

      <div className="mb-6 flex items-center gap-3">
        <Badge className={statusColors[status] ?? "bg-gray-100 text-gray-700"}>
          {status}
        </Badge>
        <span className="text-sm text-[var(--text-muted)]">
          {c?.opportunity_id}
        </span>
        {c?.effective_date && (
          <span className="text-sm text-[var(--text-muted)]">
            Effective: {new Date(c.effective_date).toLocaleDateString()}
          </span>
        )}
        {c?.expiry_date && (
          <span className="text-sm text-[var(--text-muted)]">
            Expiry: {new Date(c.expiry_date).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Parties */}
      {c?.parties && c.parties.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Parties</h3>
          <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Signatory</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {c.parties.map((p, i) => (
                  <tr key={i} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3">
                      <Badge className={p.role === "provider" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}>
                        {p.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{p.contact_email || "-"}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{p.signatory_name || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Obligations */}
      {c?.obligations && c.obligations.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Obligations</h3>
          <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--bg-secondary)] text-left text-xs uppercase text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Owner</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {c.obligations.map((o, i) => (
                  <tr key={i} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3">{o.description}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">{o.owner || "-"}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {o.due_date ? new Date(o.due_date).toLocaleDateString() : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={o.status === "fulfilled" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"}>
                        {o.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Renewal Rules */}
      {c?.renewal && (
        <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Renewal Rules</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-[var(--text-muted)]">Auto-renew:</span> {c.renewal.auto_renew ? "Yes" : "No"}</div>
            <div><span className="text-[var(--text-muted)]">Notice period:</span> {c.renewal.notice_days} days</div>
            <div><span className="text-[var(--text-muted)]">Term:</span> {c.renewal.renewal_term_months} months</div>
            <div><span className="text-[var(--text-muted)]">Max renewals:</span> {c.renewal.max_renewals === 0 ? "Unlimited" : c.renewal.max_renewals}</div>
          </div>
        </div>
      )}

      {/* Legal */}
      {(c?.legal_terms || c?.governing_law) && (
        <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Legal</h3>
          {c.legal_terms && <p className="text-sm text-[var(--text-muted)]">{c.legal_terms}</p>}
          {c.governing_law && <p className="text-sm text-[var(--text-muted)]">Governing law: {c.governing_law}</p>}
        </div>
      )}

      {/* Signatures */}
      {(c?.signed_by_provider || c?.signed_by_customer) && (
        <div className="mb-6 rounded-lg border border-[var(--border-default)] p-4">
          <h3 className="mb-2 text-sm font-medium text-[var(--text-primary)]">Signatures</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {c.signed_by_provider && <div><span className="text-[var(--text-muted)]">Provider:</span> {c.signed_by_provider}</div>}
            {c.signed_by_customer && <div><span className="text-[var(--text-muted)]">Customer:</span> {c.signed_by_customer}</div>}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {status === "DRAFT" && (
          <button
            onClick={() => action.mutate("sign")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-info,#3b82f6)] px-4 py-2 text-sm text-white hover:bg-[var(--status-info-hover,#2563eb)] disabled:opacity-50"
          >
            <FileSignature className="h-4 w-4" /> Sign
          </button>
        )}
        {status === "ACTIVE" && (
          <>
            <button
              onClick={() => action.mutate("complete")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--status-success,#16a34a)] px-4 py-2 text-sm text-white hover:bg-[var(--status-success-hover,#15803d)] disabled:opacity-50"
            >
              <Check className="h-4 w-4" /> Complete
            </button>
            <button
              onClick={() => action.mutate("terminate")}
              disabled={action.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--status-danger-border,#fecaca)] px-4 py-2 text-sm text-[var(--status-danger,#991b1b)] hover:bg-[var(--status-danger-bg,#fef2f2)] disabled:opacity-50"
            >
              <X className="h-4 w-4" /> Terminate
            </button>
          </>
        )}
        {["EXPIRED", "ACTIVE"].includes(status) && (
          <button
            onClick={() => action.mutate("renew")}
            disabled={action.isPending}
            className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border-default)] px-4 py-2 text-sm hover:bg-[var(--bg-hover)] disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" /> Renew
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
