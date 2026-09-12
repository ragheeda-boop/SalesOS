"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContact, searchCompanies, type Contact } from "@/lib/api";
import { companyKeys, contactKeys } from "@/lib/queryKeys";
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
    if (res?.status === 403) return "You don't have permission to create contacts.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create contact.";
}

function companyLabel(nameEn: string | null | undefined, nameAr: string | undefined, id: string): string {
  return nameEn?.trim() || nameAr?.trim() || id;
}

export function CreateContactForm({ onCancel }: { onCancel?: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [position, setPosition] = useState("");

  const companiesQuery = useQuery({
    queryKey: companyKeys.list(COMPANY_LIST_PARAMS as Record<string, unknown>),
    queryFn: () => searchCompanies(COMPANY_LIST_PARAMS, getTenantId()),
    staleTime: 10_000,
  });

  const companies = companiesQuery.data?.items ?? [];
  const canSubmit = Boolean(name.trim() && companyId);

  const createMutation = useMutation({
    mutationFn: () =>
      createContact(
        {
          name: name.trim(),
          company_id: companyId,
          email: email.trim() || undefined,
          phone: phone.trim() || undefined,
          position: position.trim() || undefined,
        },
        getTenantId()
      ),
    onSuccess: (contact: Contact) => {
      void queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      if (contact?.id) {
        router.push(`/v3/contacts/${contact.id}`);
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
      <h2 className="text-sm font-medium text-[var(--text-primary)]">New contact</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/contacts — required name and company_id. Empty optional fields stay empty.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
            className={INPUT_CLASS}
            data-testid="create-contact-name"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Company</span>
          <select
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            required
            className={INPUT_CLASS}
            data-testid="create-contact-company"
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
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            className={INPUT_CLASS}
            data-testid="create-contact-email"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Phone</span>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            autoComplete="tel"
            className={INPUT_CLASS}
            data-testid="create-contact-phone"
          />
        </label>
        <label className="block sm:col-span-2">
          <span className="mb-1 block text-[12px] text-[var(--text-muted)]">Position</span>
          <input
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            autoComplete="organization-title"
            className={INPUT_CLASS}
            data-testid="create-contact-position"
          />
        </label>
      </div>
      {companiesQuery.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          Could not load companies for company_id. Retry or create a company in v3 first.
        </p>
      ) : null}
      {!companiesQuery.isLoading && !companiesQuery.isError && companies.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-contact-no-companies">
          No companies in this tenant. Create a company first — POST /api/v1/contacts requires
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
          data-testid="create-contact-submit"
        >
          {createMutation.isPending ? "Creating…" : "Create contact"}
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
