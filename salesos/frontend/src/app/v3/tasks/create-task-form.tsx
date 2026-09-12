"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTask,
  listOpportunities,
  searchCompanies,
  type TaskResponse,
} from "@/lib/api";
import { companyKeys, opportunityKeys, taskKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

const COMPANY_LIST_PARAMS = {
  page: 1,
  page_size: 50,
  sort_by: "name_ar",
  sort_order: "asc" as const,
};

const PRIORITIES = ["critical", "high", "medium", "low"] as const;

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create tasks.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create task.";
}

function companyLabel(nameEn: string | null | undefined, nameAr: string | undefined, id: string): string {
  return nameEn?.trim() || nameAr?.trim() || id;
}

export function CreateTaskForm({ onCancel }: { onCancel?: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<(typeof PRIORITIES)[number]>("medium");
  const [source, setSource] = useState("manual");
  const [companyId, setCompanyId] = useState("");
  const [opportunityId, setOpportunityId] = useState("");
  const [dueDate, setDueDate] = useState("");

  const companiesQuery = useQuery({
    queryKey: companyKeys.list(COMPANY_LIST_PARAMS as Record<string, unknown>),
    queryFn: () => searchCompanies(COMPANY_LIST_PARAMS, getTenantId()),
    staleTime: 10_000,
  });

  const opportunitiesQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    staleTime: 10_000,
  });

  const companies = companiesQuery.data?.items ?? [];
  const opportunities = opportunitiesQuery.data?.items ?? [];
  const canSubmit = Boolean(title.trim());

  const createMutation = useMutation({
    mutationFn: () =>
      createTask(
        getTenantId(),
        title.trim(),
        priority,
        companyId || undefined,
        source.trim() || undefined,
        opportunityId || undefined,
        dueDate || undefined
      ),
    onSuccess: (task: TaskResponse) => {
      void queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      if (task?.id) {
        router.push(`/v3/tasks/${task.id}`);
      }
    },
  });

  return (
    <form
      className="space-y-3 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!canSubmit || createMutation.isPending) return;
        createMutation.mutate();
      }}
    >
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New task</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/tasks — required title. Priority defaults to medium, source to manual. Company,
        opportunity, and due date are optional.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-task-title"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Priority</span>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as (typeof PRIORITIES)[number])}
            className={INPUT_CLASS}
            data-testid="create-task-priority"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Source</span>
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-task-source"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Company (optional)</span>
          <select
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            className={INPUT_CLASS}
            data-testid="create-task-company"
            disabled={companiesQuery.isLoading}
          >
            <option value="">
              {companiesQuery.isLoading ? "Loading companies…" : "None"}
            </option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {companyLabel(company.name_en, company.name_ar, company.id)}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Opportunity (optional)</span>
          <select
            value={opportunityId}
            onChange={(e) => setOpportunityId(e.target.value)}
            className={INPUT_CLASS}
            data-testid="create-task-opportunity"
            disabled={opportunitiesQuery.isLoading}
          >
            <option value="">
              {opportunitiesQuery.isLoading ? "Loading deals…" : "None"}
            </option>
            {opportunities.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opp.name?.trim() || opp.id}
              </option>
            ))}
          </select>
        </label>
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Due date (optional)</span>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className={INPUT_CLASS}
            data-testid="create-task-due-date"
          />
        </label>
      </div>
      {companiesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load companies for optional company_id. You can still create a task without one.
        </p>
      ) : null}
      {opportunitiesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load deals for optional opportunity_id. You can still create a task without one.
        </p>
      ) : null}
      {!companiesQuery.isLoading && !companiesQuery.isError && companies.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-task-no-companies">
          No companies in this tenant. company_id is optional.{" "}
          <Link
            href="/v3/companies"
            className="underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Create company
          </Link>
        </p>
      ) : null}
      {createMutation.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          {createErrorMessage(createMutation.error)}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={!canSubmit || createMutation.isPending}
          className="rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          data-testid="create-task-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create task"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
