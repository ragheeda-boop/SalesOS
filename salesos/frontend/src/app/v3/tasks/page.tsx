"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { completeTask, listTasks, type TaskResponse } from "@/lib/api";
import { taskKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { openV3AiPopup } from "@/components/v3/V3AiPopup";
import { PageHeader } from "../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { formatWhen } from "../_components/format";
import { useAccessToken } from "../_hooks/useAccessToken";

const PRIORITY_FILTERS = [
  { label: "All", value: "" },
  { label: "Critical", value: "critical" },
  { label: "High", value: "high" },
  { label: "Medium", value: "medium" },
  { label: "Low", value: "low" },
] as const;

type StatusFilter = "all" | "open" | "done";

function priorityLabel(priority: string | undefined): string {
  if (!priority) return "—";
  return priority.replace(/_/g, " ");
}

export default function V3TasksPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [q, setQ] = useState("");

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: taskKeys.list(priority ? { priority } : undefined),
    queryFn: () => listTasks(getTenantId(), priority || undefined),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  const completeMutation = useMutation({
    mutationFn: (taskId: string) => completeTask(taskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });

  const items = data ?? [];

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return items.filter((task: TaskResponse) => {
      if (status === "open" && task.completed) return false;
      if (status === "done" && !task.completed) return false;
      if (!needle) return true;
      const hay =
        `${task.title} ${task.priority} ${task.source} ${task.company_id ?? ""}`.toLowerCase();
      return hay.includes(needle);
    });
  }, [items, q, status]);

  const openCount = items.filter((t) => !t.completed).length;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Tasks"
        description="Revenue tasks from GET /api/v1/tasks — Design Program v3. No fake rows; empty is honest. There is no dedicated legacy /tasks page."
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => openV3AiPopup({ contextLabel: "Tasks" })}
              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
            >
              Ask AI
            </button>
            <GhostButtonLink href="/v3/activities">Activities</GhostButtonLink>
            <GhostButtonLink href="/v3/companies">Companies</GhostButtonLink>
          </div>
        }
      />

      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/tasks" />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center">
              <label className="block min-w-0 flex-1">
                <span className="sr-only">Search tasks</span>
                <input
                  type="search"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search title, priority, source…"
                  className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                />
              </label>
              <div
                className="flex gap-1 overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border-default)] px-1 py-0.5"
                role="group"
                aria-label="Filter by priority"
              >
                {PRIORITY_FILTERS.map((f) => {
                  const selected = priority === f.value;
                  return (
                    <button
                      key={f.value || "all"}
                      type="button"
                      onClick={() => setPriority(f.value)}
                      className={
                        selected
                          ? "rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-2.5 py-1 text-[12px] font-medium text-[var(--text-primary)]"
                          : "rounded-[var(--radius-sm)] px-2.5 py-1 text-[12px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      }
                    >
                      {f.label}
                    </button>
                  );
                })}
              </div>
              <div
                className="flex gap-1 rounded-[var(--radius-md)] border border-[var(--border-default)] px-1 py-0.5"
                role="group"
                aria-label="Filter by status"
              >
                {(
                  [
                    { id: "all", label: "All" },
                    { id: "open", label: "Open" },
                    { id: "done", label: "Done" },
                  ] as const
                ).map((f) => {
                  const selected = status === f.id;
                  return (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => setStatus(f.id)}
                      className={
                        selected
                          ? "rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-2.5 py-1 text-[12px] font-medium text-[var(--text-primary)]"
                          : "rounded-[var(--radius-sm)] px-2.5 py-1 text-[12px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      }
                    >
                      {f.label}
                    </button>
                  );
                })}
              </div>
            </div>
            <p
              className="text-[12px] text-[var(--text-muted)]"
              aria-live="polite"
            >
              {isFetching && !isLoading ? "Updating… · " : null}
              {!isLoading && !isError
                ? `${filtered.length} shown · ${openCount} open of ${items.length}`
                : null}
            </p>
          </div>

          {isLoading ? (
            <LoadingState label="Loading tasks…" />
          ) : isError ? (
            <ErrorState
              title="Could not load tasks"
              description={
                error instanceof Error ? error.message : "Request failed"
              }
              onRetry={() => void refetch()}
            />
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No tasks found"
              description={
                q || priority || status !== "all"
                  ? "Try clearing search or filters. Empty results are honest — nothing is invented."
                  : "GET /api/v1/tasks returned no rows for this tenant."
              }
              action={
                q || priority || status !== "all" ? (
                  <button
                    type="button"
                    onClick={() => {
                      setQ("");
                      setPriority("");
                      setStatus("all");
                    }}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                  >
                    Clear filters
                  </button>
                ) : (
                  <GhostButtonLink href="/v3/companies">
                    Browse companies
                  </GhostButtonLink>
                )
              }
            />
          ) : (
            <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] border-collapse text-left text-sm">
                  <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                    <tr>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Title
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Priority
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Status
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Company
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Created
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((task) => (
                      <tr
                        key={task.id}
                        className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                      >
                        <td className="px-3 py-2.5">
                          <Link
                            href={`/v3/tasks/${task.id}`}
                            className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                          >
                            {task.title?.trim() || "Untitled task"}
                          </Link>
                          <p className="mt-0.5 text-[12px] text-[var(--text-muted)]">
                            {task.source || "—"}
                          </p>
                        </td>
                        <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                          {priorityLabel(task.priority)}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {task.completed ? "Done" : "Open"}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {task.company_id ? (
                            <Link
                              href={`/v3/companies/${task.company_id}`}
                              className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                            >
                              Company 360
                            </Link>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {formatWhen(task.created_at)}
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          {!task.completed ? (
                            <button
                              type="button"
                              disabled={completeMutation.isPending}
                              onClick={() => completeMutation.mutate(task.id)}
                              className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-2.5 py-1 text-[12px] text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] disabled:opacity-50"
                            >
                              Complete
                            </button>
                          ) : null}
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
