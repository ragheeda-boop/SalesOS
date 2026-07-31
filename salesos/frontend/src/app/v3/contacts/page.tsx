"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "@salesos/hooks";
import { searchContacts, type Contact } from "@/lib/api";
import { contactKeys } from "@/lib/queryKeys";
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

function contactDisplayName(c: Contact): string {
  return c.name?.trim() || c.name_ar?.trim() || "Untitled";
}

export default function V3ContactsPage() {
  const { ready, hasToken } = useAccessToken();
  const [q, setQ] = useState("");
  const debouncedQ = useDebounce(q, 400);

  const params = useMemo(
    () => ({
      q: debouncedQ || undefined,
      page: 1,
      page_size: 50,
    }),
    [debouncedQ],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: contactKeys.list(params as Record<string, unknown>),
    queryFn: () => searchContacts(params, getTenantId()),
    enabled: ready && hasToken,
    staleTime: 10_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Contacts"
        description="Customer contacts — Design Program v3. Legacy /contacts is unchanged."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/companies">Companies</GhostButtonLink>
            <GhostButtonLink href="/contacts">
              Open legacy contacts
            </GhostButtonLink>
          </div>
        }
      />

      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/contacts" />
      ) : (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="block min-w-0 flex-1">
              <span className="sr-only">Search contacts</span>
              <input
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search by name, email, or phone…"
                className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
              />
            </label>
            <p
              className="text-[12px] text-[var(--text-muted)]"
              aria-live="polite"
            >
              {isFetching && !isLoading ? "Updating… · " : null}
              {!isLoading && !isError
                ? `${total} result${total === 1 ? "" : "s"}`
                : null}
            </p>
          </div>

          {isLoading ? (
            <LoadingState label="Loading contacts…" />
          ) : isError ? (
            <ErrorState
              title="Could not load contacts"
              description={
                error instanceof Error ? error.message : "Request failed"
              }
              onRetry={() => void refetch()}
            />
          ) : items.length === 0 ? (
            <EmptyState
              title="No contacts found"
              description={
                debouncedQ
                  ? "Try a different search, or clear the filter."
                  : "No contacts in this tenant yet. Add them from legacy contacts or a company record."
              }
              action={
                debouncedQ ? (
                  <button
                    type="button"
                    onClick={() => setQ("")}
                    className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
                  >
                    Clear search
                  </button>
                ) : (
                  <GhostButtonLink href="/contacts">
                    Open legacy contacts
                  </GhostButtonLink>
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
                        Company
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Position
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Email
                      </th>
                      <th scope="col" className="px-3 py-2.5 font-medium">
                        Phone
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((contact) => (
                      <tr
                        key={contact.id}
                        className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                      >
                        <td className="px-3 py-2.5">
                          <Link
                            href={`/v3/contacts/${contact.id}`}
                            className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                          >
                            {contactDisplayName(contact)}
                          </Link>
                          {contact.is_primary ? (
                            <p className="mt-0.5 text-[12px] text-[var(--text-muted)]">
                              Primary
                            </p>
                          ) : null}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {contact.company_id ? (
                            <Link
                              href={`/v3/companies/${contact.company_id}`}
                              className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                            >
                              {contact.company_name || "View company"}
                            </Link>
                          ) : (
                            contact.company_name || "—"
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {contact.position || "—"}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {contact.email || "—"}
                        </td>
                        <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                          {contact.mobile || contact.phone || "—"}
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
