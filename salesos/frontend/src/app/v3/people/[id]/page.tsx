"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getEmployee360,
  type ActivityIntelligence,
  type EmployeeKPIs,
  type EmployeePortfolio,
  type EmployeeProfile,
} from "@/lib/api";
import { employeeKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../../_components/page-header";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
} from "../../_components/states";
import { useAccessToken } from "../../_hooks/useAccessToken";
import { openV3AiPopup } from "@/components/v3/V3AiPopup";
import { EmployeeTimeline } from "@/components/employee-360/employee-360-timeline";
import { EmployeeScoring } from "@/components/employee-360/employee-360-scoring";
import { EmployeeSignals } from "@/components/employee-360/employee-360-signals";

type TabId = "overview" | "portfolio" | "activity" | "timeline" | "intelligence";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "portfolio", label: "Portfolio" },
  { id: "activity", label: "Activity" },
  { id: "timeline", label: "Timeline" },
  { id: "intelligence", label: "Intelligence" },
];

function displayName(profile: EmployeeProfile): string {
  return profile.full_name?.trim() || profile.full_name_ar || "Person";
}

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

function formatValue(value: number | undefined | null, currency = "SAR"): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-SA", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value: number | undefined | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  const pct = value <= 1 ? value * 100 : value;
  return `${Math.round(pct)}%`;
}

function asRecord(item: unknown): Record<string, unknown> | null {
  if (item && typeof item === "object" && !Array.isArray(item)) {
    return item as Record<string, unknown>;
  }
  return null;
}

function recordId(item: Record<string, unknown>): string | undefined {
  const id = item.id;
  return typeof id === "string" ? id : undefined;
}

function recordLabel(item: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const v = item[key];
    if (typeof v === "string" && v.trim()) return v;
  }
  return "Untitled";
}

function OverviewTab({ profile, kpis }: { profile: EmployeeProfile; kpis: EmployeeKPIs }) {
  return (
    <div className="space-y-6">
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Full name" value={profile.full_name} />
        <Field label="Arabic name" value={profile.full_name_ar} />
        <Field label="Email" value={profile.email} />
        <Field label="Phone" value={profile.phone} />
        <Field label="Role" value={profile.role?.replace(/_/g, " ")} />
        <Field label="Status" value={profile.is_active ? "Active" : "Inactive"} />
        <Field
          label="Manager"
          value={profile.manager ? recordLabel(profile.manager, "full_name", "name") : null}
        />
        <Field label="Team size" value={profile.team?.length ? profile.team.length : null} />
        <Field label="Created" value={profile.created_at} />
      </dl>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">KPIs</h2>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Revenue" value={formatValue(kpis.revenue)} />
          <Field label="Pipeline" value={formatValue(kpis.pipeline)} />
          <Field label="Win rate" value={formatPct(kpis.win_rate)} />
          <Field label="Activities" value={kpis.activities} />
          <Field label="Response rate" value={formatPct(kpis.response_rate)} />
          <Field label="Follow-up rate" value={formatPct(kpis.follow_up_rate)} />
          <Field label="Productivity" value={formatPct(kpis.productivity)} />
          <Field label="Forecast" value={formatValue(kpis.forecast)} />
        </dl>
      </section>

      {profile.team?.length ? (
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-[var(--text-primary)]">Team</h2>
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {profile.team.slice(0, 12).map((member, idx) => {
              const row = asRecord(member);
              const id = row ? recordId(row) : undefined;
              const name = row ? recordLabel(row, "full_name", "name") : "Member";
              return (
                <li key={id ?? `team-${idx}`} className="px-3 py-2 text-sm">
                  {id ? (
                    <Link
                      href={`/v3/people/${id}`}
                      className="font-medium hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {name}
                    </Link>
                  ) : (
                    <span className="font-medium">{name}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function PortfolioTab({
  portfolio,
  employeeId,
}: {
  portfolio: EmployeePortfolio;
  employeeId: string;
}) {
  const companies = portfolio.companies ?? [];
  const pipeline = portfolio.pipeline ?? [];
  const contracts = portfolio.contracts ?? [];
  const contacts = portfolio.contacts ?? [];

  if (!companies.length && !pipeline.length && !contracts.length && !contacts.length) {
    return (
      <TabEmpty
        title="No portfolio yet"
        description="Companies, pipeline, and contracts for this person are empty on the 360 payload."
        ctaHref={`/employees/${employeeId}`}
        ctaLabel="Open legacy employee 360"
      />
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-[12px] text-[var(--text-muted)]">
        Revenue {formatValue(portfolio.revenue)} · {pipeline.length} pipeline item
        {pipeline.length === 1 ? "" : "s"} · {companies.length} compan
        {companies.length === 1 ? "y" : "ies"}
      </p>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Pipeline</h2>
        {pipeline.length ? (
          <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] border-collapse text-left text-sm">
                <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                  <tr>
                    <th scope="col" className="px-3 py-2.5 font-medium">
                      Deal
                    </th>
                    <th scope="col" className="px-3 py-2.5 font-medium">
                      Company
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
                  {pipeline.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
                    >
                      <td className="px-3 py-2.5 font-medium">
                        <Link
                          href={`/v3/crm/${item.id}`}
                          className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                        >
                          {item.name}
                        </Link>
                      </td>
                      <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                        {item.company_id ? (
                          <Link
                            href={`/v3/companies/${item.company_id}`}
                            className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                          >
                            {item.company_name || "Company"}
                          </Link>
                        ) : (
                          item.company_name || "—"
                        )}
                      </td>
                      <td className="px-3 py-2.5 tabular-nums text-[var(--text-secondary)]">
                        {formatValue(item.value)}
                      </td>
                      <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
                        {item.status?.replace(/_/g, " ") || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No pipeline items on this record.</p>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Companies</h2>
        {companies.length ? (
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {companies.map((raw, idx) => {
              const row = asRecord(raw);
              const id = row ? recordId(row) : undefined;
              const name = row
                ? recordLabel(row, "name_en", "name", "name_ar", "full_name")
                : "Company";
              return (
                <li key={id ?? `co-${idx}`} className="px-3 py-2 text-sm">
                  {id ? (
                    <Link
                      href={`/v3/companies/${id}`}
                      className="font-medium hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {name}
                    </Link>
                  ) : (
                    <span className="font-medium">{name}</span>
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No companies on this record.</p>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Contracts</h2>
        <p className="text-[12px] text-[var(--text-muted)]">
          Portfolio contracts from Employee 360 — no Contracts list/detail dual-run yet (commercial
          API is create/sign only).
        </p>
        {contracts.length ? (
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {contracts.map((c) => (
              <li
                key={c.id}
                className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
              >
                <span className="font-medium">{c.name}</span>
                <span className="text-[12px] text-[var(--text-muted)]">
                  {formatValue(c.value)} · {c.status?.replace(/_/g, " ") || "—"}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">No contracts on this record.</p>
        )}
      </section>

      {contacts.length ? (
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-[var(--text-primary)]">Contacts</h2>
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {contacts.map((raw, idx) => {
              const row = asRecord(raw);
              const id = row ? recordId(row) : undefined;
              const name = row ? recordLabel(row, "name", "full_name") : "Contact";
              return (
                <li key={id ?? `ct-${idx}`} className="px-3 py-2 text-sm font-medium">
                  {name}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function ActivityTab({
  activity,
  employeeId,
}: {
  activity: ActivityIntelligence;
  employeeId: string;
}) {
  const recent = activity.recent ?? [];

  if (!activity.total && !recent.length) {
    return (
      <TabEmpty
        title="No activity counts yet"
        description="Activity intelligence on the 360 payload is empty. Timeline detail stays on the legacy employee surface."
        ctaHref={`/employees/${employeeId}`}
        ctaLabel="Open legacy employee 360"
      />
    );
  }

  return (
    <div className="space-y-6">
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Total" value={activity.total} />
        <Field label="Meetings" value={activity.meetings} />
        <Field label="Emails" value={activity.emails} />
        <Field label="Calls" value={activity.calls} />
        <Field label="Tasks" value={activity.tasks} />
        <Field label="Notes" value={activity.notes} />
        <Field label="Documents" value={activity.documents} />
      </dl>

      <p className="text-sm text-[var(--text-secondary)]">
        Task counts above are activity-intelligence tallies (not the revenue tasks table).{" "}
        <Link
          href="/v3/tasks"
          className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        >
          Open Tasks
        </Link>
      </p>

      <section className="space-y-2">
        <h2 className="text-sm font-medium text-[var(--text-primary)]">Recent</h2>
        {recent.length ? (
          <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
            {recent.map((raw, idx) => {
              const row = asRecord(raw);
              const id = row ? recordId(row) : undefined;
              const title = row
                ? recordLabel(row, "title", "action", "summary", "name")
                : "Activity";
              const when =
                row && typeof row.timestamp === "string"
                  ? row.timestamp
                  : row && typeof row.created_at === "string"
                    ? row.created_at
                    : null;
              return (
                <li key={id ?? `act-${idx}`} className="px-3 py-2 text-sm">
                  <p className="font-medium text-[var(--text-primary)]">{title}</p>
                  {when ? (
                    <p className="mt-0.5 text-[12px] text-[var(--text-muted)]">{when}</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-[var(--text-secondary)]">
            Counts are present, but no recent activity rows were returned.
          </p>
        )}
      </section>
    </div>
  );
}

export default function V3People360Page() {
  const params = useParams();
  const id = String(params.id ?? "");
  const { ready, hasToken } = useAccessToken();
  const [tab, setTab] = useState<TabId>("overview");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: employeeKeys.detail(id),
    queryFn: () => getEmployee360(id, getTenantId()),
    enabled: ready && hasToken && !!id,
    staleTime: 30_000,
  });

  const profile = data?.profile;
  const title = profile ? displayName(profile) : "People 360";
  const nextPath = `/v3/people/${id}`;
  const legacyHref = `/employees/${id}`;

  const tabBody = useMemo(() => {
    if (!data) return null;
    switch (tab) {
      case "overview":
        return <OverviewTab profile={data.profile} kpis={data.kpis} />;
      case "portfolio":
        return <PortfolioTab portfolio={data.portfolio} employeeId={data.profile.id} />;
      case "activity":
        return <ActivityTab activity={data.activity_intelligence} employeeId={data.profile.id} />;
      case "timeline":
        return (
          <div className="space-y-4">
            <p className="text-[12px] text-[var(--text-muted)]">
              سجل النشاطات الكامل للموظف — Timeline
            </p>
            <EmployeeTimeline employeeId={data.profile.id} />
          </div>
        );
      case "intelligence":
        return (
          <div className="space-y-6">
            <section>
              <h2 className="text-sm font-medium text-[var(--text-primary)] mb-3">التقييم</h2>
              <EmployeeScoring employeeId={data.profile.id} />
            </section>
            <section>
              <h2 className="text-sm font-medium text-[var(--text-primary)] mb-3">الإشارات</h2>
              <EmployeeSignals employeeId={data.profile.id} />
            </section>
          </div>
        );
      default:
        return null;
    }
// eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, tab, legacyHref]);

  return (
    <div className="mx-auto max-w-6xl">
      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <>
          <PageHeader title="People 360" description="Sign in to load this person." />
          <PermissionState nextPath={nextPath} />
        </>
      ) : isLoading ? (
        <>
          <PageHeader title="People 360" />
          <LoadingState label="Loading person…" />
        </>
      ) : isError || !data || !profile ? (
        <>
          <PageHeader
            title="People 360"
            actions={
              <Link
                href="/v3/people"
                className="text-sm text-[var(--text-secondary)] hover:underline"
              >
                Back to people
              </Link>
            }
          />
          <ErrorState
            title="Could not load person"
            description={
              error instanceof Error ? error.message : "Person not found or request failed"
            }
            onRetry={() => void refetch()}
          />
        </>
      ) : (
        <>
          <PageHeader
            title={title}
            description={
              [profile.role?.replace(/_/g, " "), profile.email].filter(Boolean).join(" · ") ||
              undefined
            }
            badge={
              <span className="flex flex-wrap items-center gap-1.5">
                <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]">
                  {profile.is_active ? "Active" : "Inactive"}
                </span>
                {profile.full_name_ar ? (
                  <span
                    className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]"
                    dir="auto"
                  >
                    {profile.full_name_ar}
                  </span>
                ) : null}
              </span>
            }
            actions={
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => openV3AiPopup({ contextLabel: displayName(profile) })}
                  className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                >
                  Ask AI
                </button>
                <GhostButtonLink href="/v3/people">Back to list</GhostButtonLink>
                <GhostButtonLink href={legacyHref} primary>
                  Legacy employee 360
                </GhostButtonLink>
              </div>
            }
          />

          <div
            role="tablist"
            aria-label="People 360 sections"
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
                  id={`v3-people-tab-${t.id}`}
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

          <div role="tabpanel" aria-labelledby={`v3-people-tab-${tab}`}>
            {tabBody}
          </div>
        </>
      )}
    </div>
  );
}
