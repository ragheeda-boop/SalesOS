"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getCompany,
  getEntityActivities,
  getOpportunity,
  listOpportunities,
  type Contact,
  type Opportunity,
} from "@/lib/api";
import { activityKeys, companyKeys, opportunityKeys } from "@/lib/queryKeys";
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

type TabId = "overview" | "activity" | "contacts";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "activity", label: "Activity" },
  { id: "contacts", label: "Contacts" },
];

function stageLabel(stage: string | undefined): string {
  if (!stage) return "—";
  return stage.replace(/_/g, " ");
}

function formatValue(value: number | undefined, currency = "SAR"): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-SA", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="space-y-0.5">
      <dt className="text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">{label}</dt>
      <dd className="text-sm text-[var(--text-primary)]">{value ?? "—"}</dd>
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

async function loadDeal(id: string, tenantId: string): Promise<Opportunity> {
  try {
    return await getOpportunity(id, tenantId);
  } catch {
    // Detail route may be unavailable; fall back to list payload (same tenant).
    const list = await listOpportunities(tenantId);
    const found = list.items.find((item) => item.id === id);
    if (!found) throw new Error("Deal not found or request failed");
    return found;
  }
}

function OverviewTab({ deal }: { deal: Opportunity }) {
  const currency = deal.currency || "SAR";
  return (
    <div className="space-y-6">
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Stage" value={stageLabel(deal.stage)} />
        <Field label="Status" value={deal.status?.replace(/_/g, " ")} />
        <Field label="Value" value={formatValue(deal.value, currency)} />
        <Field
          label="Probability"
          value={deal.probability != null ? `${Math.round(deal.probability * 100)}%` : null}
        />
        <Field label="Health" value={deal.health} />
        <Field label="Expected close" value={deal.expected_close_date} />
        <Field label="Owner" value={deal.owner_id} />
        <Field label="Company" value={deal.company_name} />
        <Field
          label="Won amount"
          value={deal.won_amount != null ? formatValue(deal.won_amount, currency) : null}
        />
        <Field label="Loss reason" value={deal.loss_reason} />
        <Field label="Created" value={deal.created_at} />
        <Field label="Updated" value={deal.updated_at} />
      </dl>

      {deal.description ? (
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-[var(--text-primary)]">Description</h2>
          <p className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap">
            {deal.description}
          </p>
        </section>
      ) : (
        <p className="text-sm text-[var(--text-secondary)]">No description on this deal record.</p>
      )}

      {deal.company_id ? (
        <p className="text-sm">
          <Link
            href={`/v3/companies/${deal.company_id}`}
            className="text-[var(--text-secondary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            Open company 360 →
          </Link>
        </p>
      ) : null}
    </div>
  );
}

function ContactsTab({
  contacts,
  companyId,
  loading,
}: {
  contacts: Contact[];
  companyId?: string;
  loading: boolean;
}) {
  if (!companyId) {
    return (
      <TabEmpty
        title="No company linked"
        description="This deal has no company_id, so contacts cannot be loaded from the account record."
        ctaHref="/v3/crm"
        ctaLabel="Back to CRM"
      />
    );
  }

  if (loading) {
    return <LoadingState label="Loading contacts…" />;
  }

  if (!contacts.length) {
    return (
      <TabEmpty
        title="No contacts yet"
        description="Contacts come from the linked company payload. None are present, or the company could not be loaded."
        ctaHref={`/v3/companies/${companyId}`}
        ctaLabel="Open company 360"
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
          <tr>
            <th className="px-3 py-2.5 font-medium">Name</th>
            <th className="px-3 py-2.5 font-medium">Position</th>
            <th className="px-3 py-2.5 font-medium">Email</th>
            <th className="px-3 py-2.5 font-medium">Phone</th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((c) => (
            <tr key={c.id} className="border-b border-[var(--border-default)] last:border-b-0">
              <td className="px-3 py-2.5 font-medium">
                <Link
                  href={`/v3/contacts/${c.id}`}
                  className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                >
                  {c.name}
                </Link>
              </td>
              <td className="px-3 py-2.5 text-[var(--text-secondary)]">{c.position || "—"}</td>
              <td className="px-3 py-2.5 text-[var(--text-secondary)]">{c.email || "—"}</td>
              <td className="px-3 py-2.5 text-[var(--text-secondary)]">{c.phone || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function V3Deal360Page() {
  const params = useParams();
  const id = String(params.id ?? "");
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = useState<TabId>("overview");

  const {
    data: deal,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: opportunityKeys.detail(id),
    queryFn: () => loadDeal(id, getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 30_000,
  });

  const companyId = deal?.company_id;
  const { data: company, isLoading: companyLoading } = useQuery({
    queryKey: companyKeys.detail(companyId ?? ""),
    queryFn: () => getCompany(companyId!, getTenantId()),
    enabled: ready && hasToken && !!companyId && tab === "contacts",
    staleTime: 30_000,
  });

  const {
    data: activity,
    isLoading: activityLoading,
    isError: activityError,
    error: activityErr,
    refetch: refetchActivity,
  } = useQuery({
    queryKey: activityKeys.entity("opportunity", id),
    queryFn: () => getEntityActivities("opportunity", id, getTenantId()),
    enabled: ready && hasToken && !!id && tab === "activity",
    staleTime: 15_000,
  });

  const title = deal?.name?.trim() || "Deal 360";
  const nextPath = `/v3/crm/${id}`;

  const tabBody = useMemo(() => {
    if (!deal) return null;
    switch (tab) {
      case "overview":
        return <OverviewTab deal={deal} />;
      case "activity":
        return (
          <ActivityFeed
            items={activity?.items ?? []}
            isLoading={activityLoading}
            isError={activityError}
            errorMessage={activityErr instanceof Error ? activityErr.message : undefined}
            onRetry={() => void refetchActivity()}
            emptyTitle="No deal activity yet"
            emptyDescription="GET /api/v1/activities/opportunity/{id} returned no rows. Empty is honest — nothing is invented."
            emptyActionHref="/v3/activities"
            emptyActionLabel="Open activities"
          />
        );
      case "contacts":
        return (
          <ContactsTab
            contacts={company?.contacts ?? []}
            companyId={deal.company_id}
            loading={!!deal.company_id && companyLoading}
          />
        );
      default:
        return null;
    }
  }, [
    deal,
    tab,
    company,
    companyLoading,
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
          <PageHeader title="Deal 360" description="Sign in to load this opportunity." />
          <PermissionState nextPath={nextPath} />
        </>
      ) : isLoading ? (
        <>
          <PageHeader title="Deal 360" />
          <LoadingState label="Loading deal…" />
        </>
      ) : isError || !deal ? (
        <>
          <PageHeader
            title="Deal 360"
            actions={
              <Link href="/v3/crm" className="text-sm text-[var(--text-secondary)] hover:underline">
                Back to CRM
              </Link>
            }
          />
          <ErrorState
            title="Could not load deal"
            description={
              error instanceof Error ? error.message : "Deal not found or request failed"
            }
            onRetry={() => void refetch()}
          />
        </>
      ) : (
        <>
          <PageHeader
            title={title}
            description={
              [stageLabel(deal.stage), deal.company_name].filter(Boolean).join(" · ") ||
              formatValue(deal.value, deal.currency || "SAR")
            }
            badge={
              <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] capitalize text-[var(--text-muted)]">
                {deal.status?.replace(/_/g, " ") || stageLabel(deal.stage)}
              </span>
            }
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => openV3AiPopup({ contextLabel: deal.name || "Deal" })}
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Ask AI
                </button>
                <GhostButtonLink href="/v3/crm">Back to CRM</GhostButtonLink>
                {deal.company_id ? (
                  <GhostButtonLink href={`/v3/companies/${deal.company_id}`}>
                    Company 360
                  </GhostButtonLink>
                ) : null}
                <GhostButtonLink href="/opportunities" primary>
                  Legacy opportunities
                </GhostButtonLink>
              </div>
            }
          />

          <div
            role="tablist"
            aria-label="Deal 360 sections"
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
                  id={`v3-deal-tab-${t.id}`}
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

          <div role="tabpanel" aria-labelledby={`v3-deal-tab-${tab}`}>
            {tabBody}
          </div>
        </>
      )}
    </div>
  );
}
