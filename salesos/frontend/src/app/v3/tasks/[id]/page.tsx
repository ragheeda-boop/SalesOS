"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { completeTask, getCompany, listTasks, type TaskResponse } from "@/lib/api";
import { companyKeys, taskKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { openV3AiPopup } from "@/components/v3/V3AiPopup";
import { PageHeader } from "../../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../../_components/states";
import { formatWhen } from "../../_components/format";
import { useAccessToken } from "../../_hooks/useAccessToken";

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">{label}</dt>
      <dd className="text-sm text-[var(--text-primary)]" dir="auto">
        {value ?? "—"}
      </dd>
    </div>
  );
}

/**
 * No GET /api/v1/tasks/{id} exists — detail resolves from listTasks (honest dual-run).
 */
export default function V3TaskDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();
  const nextPath = `/v3/tasks/${id}`;

  const {
    data: tasks,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: taskKeys.list(),
    queryFn: () => listTasks(getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 15_000,
  });

  const task: TaskResponse | undefined = useMemo(
    () => (tasks ?? []).find((t) => t.id === id),
    [tasks, id]
  );

  const companyId = task?.company_id ?? undefined;
  const {
    data: company,
    isLoading: companyLoading,
    isError: companyError,
  } = useQuery({
    queryKey: companyKeys.detail(companyId ?? ""),
    queryFn: () => getCompany(companyId!, getTenantId()),
    enabled: ready && hasToken && !!companyId,
    staleTime: 30_000,
  });

  const completeMutation = useMutation({
    mutationFn: () => completeTask(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      void queryClient.invalidateQueries({ queryKey: taskKeys.detail(id) });
    },
  });

  const companyName =
    company?.name_en?.trim() || company?.name_ar || (companyId ? "Company 360" : null);
  const title = task?.title?.trim() || "Task";

  return (
    <div className="mx-auto max-w-6xl">
      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <>
          <PageHeader title="Task" description="Sign in to load this task." />
          <PermissionState nextPath={nextPath} />
        </>
      ) : isLoading ? (
        <>
          <PageHeader title="Task" />
          <LoadingState label="Loading task…" />
        </>
      ) : isError ? (
        <>
          <PageHeader
            title="Task"
            actions={
              <Link
                href="/v3/tasks"
                className="text-sm text-[var(--text-secondary)] hover:underline"
              >
                Back to tasks
              </Link>
            }
          />
          <ErrorState
            title="Could not load tasks"
            description={
              error instanceof Error
                ? error.message
                : "List fetch failed — detail has no dedicated GET endpoint"
            }
            onRetry={() => void refetch()}
          />
        </>
      ) : !task ? (
        <>
          <PageHeader
            title="Task"
            actions={<GhostButtonLink href="/v3/tasks">Back to tasks</GhostButtonLink>}
          />
          <EmptyState
            title="Task not found"
            description="No matching row in GET /api/v1/tasks for this id. There is no GET /tasks/{id} — detail is list-resolved only."
            action={<GhostButtonLink href="/v3/tasks">Browse tasks</GhostButtonLink>}
          />
        </>
      ) : (
        <>
          <PageHeader
            title={title}
            description={`${task.completed ? "Done" : "Open"} · ${task.priority || "priority —"}`}
            badge={
              <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] capitalize text-[var(--text-muted)]">
                {task.completed ? "Done" : "Open"}
              </span>
            }
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => openV3AiPopup({ contextLabel: title })}
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Ask AI
                </button>
                {!task.completed ? (
                  <button
                    type="button"
                    disabled={completeMutation.isPending}
                    onClick={() => completeMutation.mutate()}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] disabled:opacity-50"
                  >
                    {completeMutation.isPending ? "Completing…" : "Mark complete"}
                  </button>
                ) : null}
                <GhostButtonLink href="/v3/tasks">Back to list</GhostButtonLink>
                {companyId ? (
                  <GhostButtonLink href={`/v3/companies/${companyId}`} primary>
                    Company 360
                  </GhostButtonLink>
                ) : null}
              </div>
            }
          />

          <p className="mb-4 text-[12px] text-[var(--text-muted)]">
            Detail is resolved from the tasks list API — no dedicated GET /api/v1/tasks/{"{id}"}.
          </p>

          <dl className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Field label="Title" value={task.title} />
            <Field label="Priority" value={task.priority} />
            <Field label="Status" value={task.completed ? "Done" : "Open"} />
            <Field label="Source" value={task.source} />
            <Field label="Created" value={formatWhen(task.created_at)} />
            <Field label="Task id" value={task.id} />
          </dl>

          <section className="space-y-3" aria-label="Related company">
            <h2 className="text-sm font-medium text-[var(--text-primary)]">Related company</h2>
            {!companyId ? (
              <EmptyState
                title="No company linked"
                description="This task has no company_id on the API payload."
                action={<GhostButtonLink href="/v3/companies">Browse companies</GhostButtonLink>}
              />
            ) : companyLoading ? (
              <LoadingState label="Loading company…" />
            ) : (
              <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-5">
                {companyError ? (
                  <p className="mb-3 text-sm text-[var(--text-secondary)]">
                    Company detail could not be loaded. You can still open Company 360 with the
                    linked id.
                  </p>
                ) : null}
                <p className="text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                  Account
                </p>
                <p className="mt-1 text-base font-medium text-[var(--text-primary)]" dir="auto">
                  {companyName}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <GhostButtonLink href={`/v3/companies/${companyId}`} primary>
                    Open Company 360
                  </GhostButtonLink>
                  <GhostButtonLink href={`/companies/${companyId}`}>Legacy company</GhostButtonLink>
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
