"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCompany, type Company } from "@/lib/api";
import { companyKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

const INPUT_CLASS =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]";

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create companies.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create company.";
}

export function CreateCompanyForm({ onCancel }: { onCancel?: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [nameAr, setNameAr] = useState("");
  const [crNumber, setCrNumber] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [city, setCity] = useState("");
  const [region, setRegion] = useState("");

  const canSubmit = Boolean(nameAr.trim() && crNumber.trim());

  const createMutation = useMutation({
    mutationFn: () =>
      createCompany(
        {
          name_ar: nameAr.trim(),
          cr_number: crNumber.trim(),
          name_en: nameEn.trim() || undefined,
          city: city.trim() || undefined,
          region: region.trim() || undefined,
        },
        getTenantId()
      ),
    onSuccess: (company: Company) => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
      if (company?.id) {
        router.push(`/v3/companies/${company.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New company</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/companies — required Arabic name and CR. Empty optional fields stay empty.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Arabic name</span>
          <input
            value={nameAr}
            onChange={(e) => setNameAr(e.target.value)}
            required
            autoComplete="organization"
            className={INPUT_CLASS}
            data-testid="create-company-name-ar"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">CR number</span>
          <input
            value={crNumber}
            onChange={(e) => setCrNumber(e.target.value)}
            required
            autoComplete="off"
            className={INPUT_CLASS}
            data-testid="create-company-cr"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">English name</span>
          <input
            value={nameEn}
            onChange={(e) => setNameEn(e.target.value)}
            autoComplete="organization"
            className={INPUT_CLASS}
            data-testid="create-company-name-en"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">City</span>
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            autoComplete="address-level2"
            className={INPUT_CLASS}
            data-testid="create-company-city"
          />
        </label>
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Region</span>
          <input
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            autoComplete="address-level1"
            className={INPUT_CLASS}
            data-testid="create-company-region"
          />
        </label>
      </div>
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
          data-testid="create-company-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create company"}
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
