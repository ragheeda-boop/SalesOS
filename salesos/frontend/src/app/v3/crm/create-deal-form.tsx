"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createOpportunity, searchCompanies } from "@/lib/api";
import { companyKeys, opportunityKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

const COMPANY_LIST_PARAMS = {
  page: 1,
  page_size: 50,
  sort_by: "name_ar",
  sort_order: "asc" as const,
};

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create opportunities.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create deal.";
}

function companyLabel(nameEn: string | null | undefined, nameAr: string | undefined, id: string): string {
  return nameEn?.trim() || nameAr?.trim() || id;
}

/** Query `value` is optional; empty posts the API default 0. Invalid numbers block submit. */
function parseValue(raw: string): number | null {
  const trimmed = raw.trim();
  if (!trimmed) return 0;
  const n = Number(trimmed);
  if (!Number.isFinite(n) || n < 0) return null;
  return n;
}

export function CreateDealForm({
  companyId: lockedCompanyId,
  onCancel,
}: {
  companyId?: string;
  onCancel?: () => void;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [pickedCompanyId, setPickedCompanyId] = useState("");
  const [value, setValue] = useState("");

  const companyId = lockedCompanyId || pickedCompanyId;
  const parsedValue = parseValue(value);
  const needsPicker = !lockedCompanyId;

  const companiesQuery = useQuery({
    queryKey: companyKeys.list(COMPANY_LIST_PARAMS as Record<string, unknown>),
    queryFn: () => searchCompanies(COMPANY_LIST_PARAMS, getTenantId()),
    staleTime: 10_000,
    enabled: needsPicker,
  });

  const companies = companiesQuery.data?.items ?? [];
  const canSubmit = Boolean(name.trim() && companyId && parsedValue !== null);

  const createMutation = useMutation({
    mutationFn: () => createOpportunity(getTenantId(), companyId, name.trim(), parsedValue ?? 0),
    onSuccess: (opp: { id?: string }) => {
      void queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() });
      if (opp?.id) {
        router.push(`/v3/crm/${opp.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New deal</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/opportunities — required company_id and name. Value defaults to 0.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Deal name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-deal-name"
          />
        </label>
        {needsPicker ? (
          <label className="block">
            <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Company</span>
            <select
              value={pickedCompanyId}
              onChange={(e) => setPickedCompanyId(e.target.value)}
              required
              className={INPUT_CLASS}
              data-testid="create-deal-company"
              disabled={companiesQuery.isLoading || companies.length === 0}
            >
              <option value="">
                {companiesQuery.isLoading ? "Loading companies…" : "Select a company"}
              </option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {companyLabel(company.name_en, company.name_ar, company.id)}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <p className="self-end text-[12px] text-[var(--text-muted)]" data-testid="create-deal-company-locked">
            company_id locked to this account
          </p>
        )}
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Value (SAR, optional)</span>
          <input
            type="number"
            min={0}
            step="any"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className={INPUT_CLASS}
            data-testid="create-deal-value"
          />
        </label>
      </div>
      {needsPicker && companiesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load companies for company_id. Retry or create a company in v3 first.
        </p>
      ) : null}
      {needsPicker && !companiesQuery.isLoading && !companiesQuery.isError && companies.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-deal-no-companies">
          No companies in this tenant. Create a company first — POST /api/v1/opportunities requires
          company_id.{" "}
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
          data-testid="create-deal-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create deal"}
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
