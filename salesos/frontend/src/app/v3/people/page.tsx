"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "@salesos/hooks";
import { searchEmployees } from "@/lib/api";
import { employeeKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

type StatusFilter = "all" | "active" | "inactive";

export default function V3PeoplePage() {
  const { ready, hasToken } = useAccessToken();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const debouncedQ = useDebounce(q, 400);

  const params = useMemo(
    () => ({
      q: debouncedQ || undefined,
      page_size: 50,
    }),
    [debouncedQ]
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: employeeKeys.list(params as Record<string, unknown>),
    queryFn: () => searchEmployees(params, getTenantId()),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  const rows = data?.data ?? [];
  const filtered = useMemo(() => {
    if (status === "all") return rows;
    if (status === "active") return rows.filter((e) => e.is_active);
    return rows.filter((e) => !e.is_active);
  }, [rows, status]);

  const totalLabel =
    data?.total != null
      ? `${filtered.length} shown · ${data.total} total`
      : `${filtered.length} result${filtered.length === 1 ? "" : "s"}`;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="People"
        description="Employees and owners — Design Program v3. Decision-maker graphs remain out of scope here."
        actions={<GhostButtonLink href="/employees">Open legacy people</GhostButtonLink>}
      />

      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/people" />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center">
              <label className="block min-w-0 flex-1">
                <span className="sr-only">Search people</span>
                <input
                  type="search"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search by name or email…"
                  className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <span className="shrink-0 text-[12px] text-[var(--text-muted)]">Status</span>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as StatusFilter)}
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-2.5 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                >
                  <option value="all">All</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
            </div>
            <p className="text-[12px] text-[var(--text-muted)]" aria-live="polite">
              {isFetching && !isLoading ? "Updating… · " : null}
              {!isLoading && !isError ? totalLabel : null}
            </p>
          </div>

          {isLoading ? (
            <LoadingState label="Loading people…" />
          ) : isError ? (
            <ErrorState
              title="Could not load people"
              description={error instanceof Error ? error.message : "Request failed"}
              onRetry={() => void refetch()}
            />
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No people found"
              description={
                debouncedQ || status !== "all"
                  ? "Try a different search or status filter."
                  : "No employees in this tenant yet."
              }
              action={
                debouncedQ || status !== "all" ? (
                  <button
                    type="button"
                    onClick={() => {
                      setQ("");
                      setStatus("all");
                    }}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                  >
                    Clear filters
                  </button>
                ) : (
                  <GhostButtonLink href="/employees">Open legacy people</GhostButtonLink>
                )
              }
            />
          ) : (
            <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                  <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                    <tr>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Name
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Email
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Role
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Department
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((person) => (
                      <tr
                        key={person.id}
                        className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                      >
                        <td className="px-3 py-2.5">
                          <Link
                            href={`/v3/people/${person.id}`}
                            className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                          >
                            {person.full_name || "Untitled"}
                          </Link>
                          {person.full_name_ar ? (
                            <p className="mt-0.5 text-[12px] text-[var(--text-muted)]" dir="auto">
                              {person.full_name_ar}
                            </p>
                          ) : null}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {person.email || "—"}
                        </td>
                        <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                          {person.role?.replace(/_/g, " ") || "—"}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {person.department || "—"}
                        </td>
                        <td className="px-3 py-2.5">
                          <span
                            className={
                              person.is_active
                                ? "text-[var(--text-secondary)]"
                                : "text-[var(--text-muted)]"
                            }
                          >
                            {person.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
