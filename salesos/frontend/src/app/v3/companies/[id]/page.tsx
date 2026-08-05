"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getCompany,
  getEntityActivities,
  listOpportunities,
  listTasks,
  type CompanyDetail,
  type Contact,
  type Opportunity,
  type TaskResponse,
} from "@/lib/api";
import { activityKeys, companyKeys, opportunityKeys, taskKeys } from "@/lib/queryKeys";
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
import { IntelligenceTab } from "./intelligence-tab";

type TabId = "overview" | "contacts" | "timeline" | "opportunities" | "tasks" | "intelligence";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "contacts", label: "Contacts" },
  { id: "timeline", label: "Timeline" },
  { id: "opportunities", label: "Opportunities" },
  { id: "tasks", label: "Tasks" },
  { id: "intelligence", label: "Intelligence" },
];

function displayName(company: CompanyDetail): string {
  return company.name_en?.trim() || company.name_ar || "Company";
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

function isOpenDeal(opp: Opportunity): boolean {
  const status = (opp.status || "").toLowerCase();
  if (!status) return true;
  return !(
    status.includes("won") ||
    status.includes("lost") ||
    status === "closed" ||
    status.startsWith("closed_")
  );
}

function OverviewTab({ company }: { company: CompanyDetail }) {
  return (
    <div className="space-y-6">
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Arabic name" value={company.name_ar} />
        <Field label="English name" value={company.name_en} />
        <Field label="CR number" value={company.cr_number} />
        <Field label="Status" value={company.status} />
        <Field label="City" value={company.city} />
        <Field label="Region" value={company.region} />
        <Field label="Phone" value={company.phone} />
        <Field label="Email" value={company.email} />
        <Field
          label="Confidence"
          value={
            company.confidence_score != null
              ? (() => {
                  const raw = Number(company.confidence_score);
                  if (!Number.isFinite(raw)) return null;
                  // Backend may send 0–1 ratio or already 0–100 percent.
                  const pct = raw <= 1 ? raw * 100 : raw;
                  return `${Math.round(Math.min(Math.max(pct, 0), 100))}%`;
                })()
              : null
          }
        />
      </dl>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Branches</h2>
        {company.branches?.length ? (
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {company.branches.map((b) => (
              <li key={b.id} className="px-3 py-2 text-sm">
                <span className="font-medium">{b.name}</span>
                <span className="text-[var(--text-muted)]">
                  {" "}
                  — {[b.city, b.region].filter(Boolean).join(", ") || "No location"}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No branches on this record.</p>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Licenses</h2>
        {company.licenses?.length ? (
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {company.licenses.map((lic) => (
              <li
                key={lic.id}
                className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
              >
                <span>
                  {lic.license_type} · {lic.license_number}
                </span>
                <span className="text-[12px] capitalize text-[var(--text-muted)]">
                  {lic.status}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No licenses on this record.</p>
        )}
      </section>
    </div>
  );
}

function ContactsTab({ contacts }: { contacts: Contact[] }) {
  if (!contacts.length) {
    return (
      <TabEmpty
        title="No contacts yet"
        description="Contacts for this company are empty on the detail payload. Add them in legacy contacts or the company workspace."
        ctaHref="/v3/contacts"
        ctaLabel="Browse contacts"
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

function OpportunitiesTab({
  companyId,
  items,
  isLoading,
  isError,
  error,
  onRetry,
}: {
  companyId: string;
  items: Opportunity[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  if (isLoading) {
    return <LoadingState label="Loading opportunities…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Could not load opportunities"
        description={error instanceof Error ? error.message : "Request failed"}
        onRetry={onRetry}
      />
    );
  }

  if (!items.length) {
    return (
      <TabEmpty
        title="No opportunities for this company"
        description="No deals are linked to this account yet. Create one from the CRM pipeline or the legacy company workspace."
        ctaHref="/v3/crm"
        ctaLabel="Open CRM"
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-[var(--text-muted)]">
        {items.length} deal{items.length === 1 ? "" : "s"} · open Deal 360 for detail
      </p>
      <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] border-collapse text-left text-sm">
            <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
              <tr>
                <th scope="col" className="px-3 py-2.5 font-medium">
                  Deal
                </th>
                <th scope="col" className="px-3 py-2.5 font-medium">
                  Stage
                </th>
                <th scope="col" className="px-3 py-2.5 font-medium">
                  Value
                </th>
                <th scope="col" className="px-3 py-2.5 font-medium">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((opp) => (
                <tr
                  key={opp.id}
                  className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2.5 font-medium text-[var(--text-primary)]">
                    <Link
                      href={`/v3/crm/${opp.id}`}
                      className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {opp.name}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                    {stageLabel(opp.stage)}
                  </td>
                  <td className="px-3 py-2.5 tabular-nums text-[var(--text-secondary)]">
                    {formatValue(opp.value, opp.currency || "SAR")}
                  </td>
                  <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                    {opp.status?.replace(/_/g, " ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-sm">
        <Link
          href="/v3/crm"
          className="text-[var(--text-secondary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          Browse all deals →
        </Link>
        <span className="text-[var(--text-muted)]"> · </span>
        <Link
          href={`/companies/${companyId}`}
          className="text-[var(--text-secondary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          Legacy company
        </Link>
      </p>
    </div>
  );
}

function TasksTab({
  companyId,
  items,
  isLoading,
  isError,
  error,
  onRetry,
}: {
  companyId: string;
  items: TaskResponse[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  if (isLoading) {
    return <LoadingState label="Loading tasks…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Could not load tasks"
        description={error instanceof Error ? error.message : "Request failed"}
        onRetry={onRetry}
      />
    );
  }

  if (!items.length) {
    return (
      <TabEmpty
        title="No tasks linked to this company"
        description="Filtered GET /api/v1/tasks by company_id. Empty is honest — activity-timeline “task” events are separate from the revenue tasks table."
        ctaHref="/v3/tasks"
        ctaLabel="Browse all tasks"
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-[var(--text-muted)]">
        {items.length} task{items.length === 1 ? "" : "s"} with company_id matching this account
      </p>
      <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] border-collapse text-left text-sm">
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
              </tr>
            </thead>
            <tbody>
              {items.map((task) => (
                <tr
                  key={task.id}
                  className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2.5 font-medium">
                    <Link
                      href={`/v3/tasks/${task.id}`}
                      className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {task.title?.trim() || "Untitled task"}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                    {task.priority?.replace(/_/g, " ") || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                    {task.completed ? "Done" : "Open"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-sm">
        <Link
          href="/v3/tasks"
          className="text-[var(--text-secondary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          Browse all tasks →
        </Link>
        <span className="text-[var(--text-muted)]"> · </span>
        <Link
          href={`/companies/${companyId}`}
          className="text-[var(--text-secondary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          Legacy company
        </Link>
      </p>
    </div>
  );
}

export default function V3Company360Page() {
  const params = useParams();
  const id = String(params.id ?? "");
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = useState<TabId>("overview");

  const {
    data: company,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: companyKeys.detail(id),
    queryFn: () => getCompany(id, getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 30_000,
  });

  const {
    data: opportunityList,
    isLoading: oppsLoading,
    isError: oppsError,
    error: oppsErr,
    refetch: refetchOpps,
  } = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 15_000,
  });

  const {
    data: activity,
    isLoading: activityLoading,
    isError: activityError,
    error: activityErr,
    refetch: refetchActivity,
  } = useQuery({
    queryKey: activityKeys.entity("company", id),
    queryFn: () => getEntityActivities("company", id, getTenantId()),
    enabled: ready && hasToken && !!id && tab === "timeline",
    staleTime: 15_000,
  });

  const {
    data: taskList,
    isLoading: tasksLoading,
    isError: tasksError,
    error: tasksErr,
    refetch: refetchTasks,
  } = useQuery({
    queryKey: taskKeys.list(),
    queryFn: () => listTasks(getTenantId()),
    enabled: ready && hasToken && !!id && tab === "tasks",
    staleTime: 15_000,
  });

  const companyOpps = useMemo(() => {
    const items = opportunityList?.items ?? [];
    return items.filter((opp) => opp.company_id === id);
  }, [opportunityList?.items, id]);

  const companyTasks = useMemo(() => {
    const items = taskList ?? [];
    return items.filter((task) => task.company_id === id);
  }, [taskList, id]);

  const openDealCount = useMemo(() => companyOpps.filter(isOpenDeal).length, [companyOpps]);

  const title = company ? displayName(company) : "Company 360";
  const nextPath = `/v3/companies/${id}`;

  const tabBody = useMemo(() => {
    if (!company) return null;
    switch (tab) {
      case "overview":
        return <OverviewTab company={company} />;
      case "contacts":
        return <ContactsTab contacts={company.contacts ?? []} />;
      case "timeline":
        return (
          <ActivityFeed
            items={activity?.items ?? []}
            isLoading={activityLoading}
            isError={activityError}
            errorMessage={activityErr instanceof Error ? activityErr.message : undefined}
            onRetry={() => void refetchActivity()}
            emptyTitle="No company activity yet"
            emptyDescription="GET /api/v1/activities/company/{id} returned no rows. Empty is honest — nothing is invented."
            emptyActionHref="/v3/activities"
            emptyActionLabel="Open activities"
          />
        );
      case "opportunities":
        return (
          <OpportunitiesTab
            companyId={company.id}
            items={companyOpps}
            isLoading={oppsLoading}
            isError={oppsError}
            error={oppsErr instanceof Error ? oppsErr : null}
            onRetry={() => void refetchOpps()}
          />
        );
      case "tasks":
        return (
          <TasksTab
            companyId={company.id}
            items={companyTasks}
            isLoading={tasksLoading}
            isError={tasksError}
            error={tasksErr instanceof Error ? tasksErr : null}
            onRetry={() => void refetchTasks()}
          />
        );
      case "intelligence":
        return <IntelligenceTab companyId={company.id} />;
      default:
        return null;
    }
  }, [
    company,
    tab,
    companyOpps,
    oppsLoading,
    oppsError,
    oppsErr,
    refetchOpps,
    companyTasks,
    tasksLoading,
    tasksError,
    tasksErr,
    refetchTasks,
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
          <PageHeader title="Company 360" description="Sign in to load this account." />
          <PermissionState nextPath={nextPath} />
        </>
      ) : isLoading ? (
        <>
          <PageHeader title="Company 360" />
          <LoadingState label="Loading company…" />
        </>
      ) : isError || !company ? (
        <>
          <PageHeader
            title="Company 360"
            actions={
              <Link
                href="/v3/companies"
                className="text-sm text-[var(--text-secondary)] hover:underline"
              >
                Back to companies
              </Link>
            }
          />
          <ErrorState
            title="Could not load company"
            description={
              error instanceof Error ? error.message : "Company not found or request failed"
            }
            onRetry={() => void refetch()}
          />
        </>
      ) : (
        <>
          <PageHeader
            title={title}
            description={company.name_en && company.name_ar ? company.name_ar : company.cr_number}
            badge={
              <span className="flex flex-wrap items-center gap-1.5">
                {!oppsLoading && !oppsError ? (
                  <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]">
                    {openDealCount} open deal{openDealCount === 1 ? "" : "s"}
                  </span>
                ) : null}
              </span>
            }
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => openV3AiPopup({ contextLabel: displayName(company) })}
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Ask AI
                </button>
                <GhostButtonLink href="/v3/companies">Back to list</GhostButtonLink>
                <GhostButtonLink href={`/companies/${company.id}`}>Legacy company</GhostButtonLink>
                <GhostButtonLink href={`/companies/${company.id}/360`} primary>
                  Legacy 360
                </GhostButtonLink>
              </div>
            }
          />

          <div
            role="tablist"
            aria-label="Company 360 sections"
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
                  id={`v3-company-tab-${t.id}`}
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

          <div role="tabpanel" aria-labelledby={`v3-company-tab-${tab}`}>
            {tabBody}
          </div>
        </>
      )}
    </div>
  );
}
