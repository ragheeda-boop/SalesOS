"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getCompany,
  getContact,
  getEntityActivities,
  type Contact,
} from "@/lib/api";
import { activityKeys, companyKeys, contactKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../../_components/page-header";
import { ActivityFeed } from "../../_components/activity-feed";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import { openV3AiPopup } from "@/components/v3/V3AiPopup";

type TabId = "overview" | "company" | "activity";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "company", label: "Company" },
  { id: "activity", label: "Activity" },
];

function displayName(contact: Contact): string {
  return contact.name?.trim() || contact.name_ar?.trim() || "Contact";
}

function Field({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="space-y-0.5">
      <dt className="text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
        {label}
      </dt>
      <dd className="text-sm text-[var(--text-primary)]" dir="auto">
        {value ?? "—"}
      </dd>
    </div>
  );
}

function TabEmpty({
  title,
  description,
  ctaHref,
  ctaLabel,
}: {
  title: string;
  description: string;
  ctaHref: string;
  ctaLabel: string;
}) {
  return (
    <EmptyState
      title={title}
      description={description}
      action={<GhostButtonLink href={ctaHref}>{ctaLabel}</GhostButtonLink>}
    />
  );
}

function OverviewTab({ contact }: { contact: Contact }) {
  return (
    <div className="space-y-6">
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Name" value={contact.name} />
        <Field label="Arabic name" value={contact.name_ar} />
        <Field label="Position" value={contact.position} />
        <Field label="Position (AR)" value={contact.position_ar} />
        <Field label="Department" value={contact.department} />
        <Field label="Email" value={contact.email} />
        <Field label="Phone" value={contact.phone} />
        <Field label="Mobile" value={contact.mobile} />
        <Field label="Source" value={contact.source} />
        <Field
          label="Primary"
          value={
            contact.is_primary == null
              ? null
              : contact.is_primary
                ? "Yes"
                : "No"
          }
        />
        <Field
          label="Confidence"
          value={
            contact.confidence_score != null
              ? `${Math.round(contact.confidence_score * 100)}%`
              : null
          }
        />
        <Field
          label="Tags"
          value={contact.tags?.length ? contact.tags.join(", ") : null}
        />
      </dl>

      {contact.company_id ? (
        <p className="text-sm text-[var(--text-secondary)]">
          Account:{" "}
          <Link
            href={`/v3/companies/${contact.company_id}`}
            className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            {contact.company_name || "Open Company 360"}
          </Link>
        </p>
      ) : null}
    </div>
  );
}

function CompanyTab({
  contact,
  companyName,
  loading,
  error,
}: {
  contact: Contact;
  companyName?: string | null;
  loading: boolean;
  error: boolean;
}) {
  if (!contact.company_id) {
    return (
      <TabEmpty
        title="No company linked"
        description="This contact has no company_id on the API payload. Link an account from legacy contacts."
        ctaHref="/contacts"
        ctaLabel="Open legacy contacts"
      />
    );
  }

  if (loading) {
    return <LoadingState label="Loading company…" />;
  }

  const label = companyName || contact.company_name || "Company 360";

  return (
    <div className="space-y-4">
      {error ? (
        <p className="text-sm text-[var(--text-secondary)]">
          Company detail could not be loaded. You can still open Company 360
          with the linked id.
        </p>
      ) : null}
      <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-5">
        <p className="text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
          Account
        </p>
        <p
          className="mt-1 text-base font-medium text-[var(--text-primary)]"
          dir="auto"
        >
          {label}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <GhostButtonLink href={`/v3/companies/${contact.company_id}`} primary>
            Open Company 360
          </GhostButtonLink>
          <GhostButtonLink href={`/companies/${contact.company_id}`}>
            Legacy company
          </GhostButtonLink>
        </div>
      </div>
    </div>
  );
}

export default function V3Contact360Page() {
  const params = useParams();
  const id = String(params.id ?? "");
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = useState<TabId>("overview");

  const {
    data: contact,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: contactKeys.detail(id),
    queryFn: () => getContact(id, getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 30_000,
  });

  const companyId = contact?.company_id ?? undefined;
  const {
    data: company,
    isLoading: companyLoading,
    isError: companyError,
  } = useQuery({
    queryKey: companyKeys.detail(companyId ?? ""),
    queryFn: () => getCompany(companyId!, getTenantId()),
    enabled: ready && hasToken && !!companyId && tab === "company",
    staleTime: 30_000,
  });

  const {
    data: activity,
    isLoading: activityLoading,
    isError: activityError,
    error: activityErr,
    refetch: refetchActivity,
  } = useQuery({
    queryKey: activityKeys.entity("contact", id),
    queryFn: () => getEntityActivities("contact", id, getTenantId()),
    enabled: ready && hasToken && !!id && tab === "activity",
    staleTime: 15_000,
  });

  const title = contact ? displayName(contact) : "Contact 360";
  const nextPath = `/v3/contacts/${id}`;

  const companyDisplay =
    company?.name_en?.trim() ||
    company?.name_ar ||
    contact?.company_name ||
    null;

  const tabBody = useMemo(() => {
    if (!contact) return null;
    switch (tab) {
      case "overview":
        return <OverviewTab contact={contact} />;
      case "company":
        return (
          <CompanyTab
            contact={contact}
            companyName={companyDisplay}
            loading={companyLoading}
            error={companyError}
          />
        );
      case "activity":
        return (
          <ActivityFeed
            items={activity?.items ?? []}
            isLoading={activityLoading}
            isError={activityError}
            errorMessage={
              activityErr instanceof Error ? activityErr.message : undefined
            }
            onRetry={() => void refetchActivity()}
            emptyTitle="No contact activity yet"
            emptyDescription="GET /api/v1/activities/contact/{id} returned no rows. Empty is honest — nothing is invented."
            emptyActionHref="/v3/activities"
            emptyActionLabel="Open activities"
          />
        );
      default:
        return null;
    }
  }, [
    contact,
    tab,
    companyDisplay,
    companyLoading,
    companyError,
    activity,
    activityLoading,
    activityError,
    activityErr,
    refetchActivity,
  ]);

  return (
    <div className="mx-auto max-w-6xl">
      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <>
          <PageHeader
            title="Contact 360"
            description="Sign in to load this contact."
          />
          <PermissionState nextPath={nextPath} />
        </>
      ) : isLoading ? (
        <>
          <PageHeader title="Contact 360" />
          <LoadingState label="Loading contact…" />
        </>
      ) : isError || !contact ? (
        <>
          <PageHeader
            title="Contact 360"
            actions={
              <Link
                href="/v3/contacts"
                className="text-sm text-[var(--text-secondary)] hover:underline"
              >
                Back to contacts
              </Link>
            }
          />
          <ErrorState
            title="Could not load contact"
            description={
              error instanceof Error
                ? error.message
                : "Contact not found or request failed"
            }
            onRetry={() => void refetch()}
          />
        </>
      ) : (
        <>
          <PageHeader
            title={title}
            description={
              [contact.position, contact.company_name]
                .filter(Boolean)
                .join(" · ") ||
              contact.email ||
              undefined
            }
            badge={
              contact.is_primary ? (
                <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]">
                  Primary
                </span>
              ) : undefined
            }
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() =>
                    openV3AiPopup({ contextLabel: displayName(contact) })
                  }
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Ask AI
                </button>
                <GhostButtonLink href="/v3/contacts">
                  Back to list
                </GhostButtonLink>
                {contact.company_id ? (
                  <GhostButtonLink href={`/v3/companies/${contact.company_id}`}>
                    Company 360
                  </GhostButtonLink>
                ) : null}
                <GhostButtonLink href="/contacts" primary>
                  Legacy contacts
                </GhostButtonLink>
              </div>
            }
          />

          <div
            role="tablist"
            aria-label="Contact 360 sections"
            className="mb-4 flex flex-wrap gap-1 border-b border-[var(--border-default)] pb-px"
          >
            {TABS.map((t) => {
              const selected = tab === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  id={`v3-contact-tab-${t.id}`}
                  onClick={() => setTab(t.id)}
                  className={
                    selected
                      ? "-mb-px border-b-2 border-[var(--muhide-orange)] px-3 py-2 text-sm font-medium text-[var(--text-primary)]"
                      : "px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }
                >
                  {t.label}
                </button>
              );
            })}
          </div>

          <div role="tabpanel" aria-labelledby={`v3-contact-tab-${tab}`}>
            {tabBody}
          </div>
        </>
      )}
    </div>
  );
}
