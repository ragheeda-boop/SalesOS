"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { decideOrgRegistration, listOrgRegistrationRequests } from "@/lib/api/identity";
import { PageHeader } from "../../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";

export default function OrgRegistrationsPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [reasonById, setReasonById] = useState<Record<string, string>>({});
  const [actionError, setActionError] = useState("");

  const query = useQuery({
    queryKey: ["org-registration-requests"],
    queryFn: listOrgRegistrationRequests,
    enabled: ready && hasToken,
  });

  const decide = useMutation({
    mutationFn: ({
      id,
      decision,
      reason,
    }: {
      id: string;
      decision: "approve" | "reject";
      reason?: string;
    }) => decideOrgRegistration(id, decision, reason),
    onSuccess: async () => {
      setActionError("");
      await queryClient.invalidateQueries({ queryKey: ["org-registration-requests"] });
    },
    onError: (err: unknown) => {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "";
      setActionError(typeof detail === "string" && detail ? detail : "Decision failed");
    },
  });

  return (
    <div className="mx-auto max-w-3xl space-y-4 p-6">
      <PageHeader
        title="Organization approvals"
        description="The platform owner approves the organization and its manager before that manager can register."
      />
      {!ready ? <LoadingState label="Checking session…" /> : null}
      {ready && !hasToken ? (
        <PermissionState
          nextPath="/admin/login"
          title="Platform owner login required"
          description="Only the designated platform owner can approve organizations and managers."
        />
      ) : null}
      {query.isLoading ? <LoadingState label="Loading requests…" /> : null}
      {query.isError ? (
        <ErrorState
          title="Could not load requests"
          description="This list is limited to the platform owner."
        />
      ) : null}
      {actionError ? <p className="text-sm text-[var(--text-danger)]">{actionError}</p> : null}
      {query.data && query.data.length === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">No open organization requests.</p>
      ) : null}
      <ul className="space-y-3">
        {(query.data ?? []).map((row) => (
          <li
            key={row.id}
            className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4"
          >
            <p className="font-medium">{row.organization_name}</p>
            <p className="text-sm text-[var(--text-secondary)]">
              {row.manager_full_name} · {row.manager_email}
            </p>
            <p className="text-xs text-[var(--text-muted)]">{row.status}</p>
            {row.status === "pending" ? (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  disabled={decide.isPending}
                  className="rounded-lg bg-[var(--muhide-orange)] px-3 py-2 text-sm text-white disabled:opacity-50"
                  onClick={() => decide.mutate({ id: row.id, decision: "approve" })}
                >
                  Approve
                </button>
                <input
                  type="text"
                  value={reasonById[row.id] ?? ""}
                  onChange={(e) =>
                    setReasonById((current) => ({ ...current, [row.id]: e.target.value }))
                  }
                  placeholder="Rejection reason"
                  className="min-w-48 flex-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                />
                <button
                  type="button"
                  disabled={decide.isPending}
                  className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm disabled:opacity-50"
                  onClick={() =>
                    decide.mutate({
                      id: row.id,
                      decision: "reject",
                      reason: reasonById[row.id] ?? "",
                    })
                  }
                >
                  Reject
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
