"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getExecutiveDashboard,
  searchCompanies,
  type Company,
} from "@/lib/api";
import { companyKeys, dashboardKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";
import { PageHeader } from "../_components/page-header";
import {
  DomainWorkbench,
  type DomainSection,
} from "../_components/domain-workbench";
import { MetricCards } from "../_components/metric-cards";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
  PermissionState,
  PreviewBadge,
} from "../_components/states";
import { formatCount, formatCurrencySAR } from "../_components/format";
import { useAccessToken } from "../_hooks/useAccessToken";

function companyDisplayName(c: Company): string {
  return c.name_en?.trim() || c.name_ar || "Untitled";
}

function PreviewPanel({
  children,
  href,
  hrefLabel = "Browse companies",
}: {
  children: ReactNode;
  href?: string;
  hrefLabel?: string;
}) {
  return (
    <div className="space-y-3 text-sm text-[var(--text-secondary)]">
      <div className="flex items-center gap-2">
        <PreviewBadge />
        <span className="text-[12px] text-[var(--text-muted)]">
          Not wired — no fake health AI
        </span>
      </div>
      <p>{children}</p>
      {href ? <GhostButtonLink href={href}>{hrefLabel}</GhostButtonLink> : null}
    </div>
  );
}

export default function V3CsPage() {
  const { ready, hasToken } = useAccessToken();
  const enabled = ready && hasToken;

  const execQuery = useQuery({
    queryKey: dashboardKeys.exec(),
    queryFn: () => getExecutiveDashboard(getTenantId()),
    enabled,
    staleTime: 60_000,
  });

  const companiesQuery = useQuery({
    queryKey: companyKeys.list({
      page: 1,
      page_size: 8,
      sort_by: "name_ar",
      sort_order: "asc",
    }),
    queryFn: () =>
      searchCompanies(
        { page: 1, page_size: 8, sort_by: "name_ar", sort_order: "asc" },
        getTenantId(),
      ),
    enabled,
    staleTime: 15_000,
  });

  const data = execQuery.data;
  const companies = companiesQuery.data?.items ?? [];

  const sections: DomainSection[] = useMemo(() => {
    const gate =
      !ready || !hasToken ? null : execQuery.isLoading ? (
        <LoadingState label="Loading CS metrics…" />
      ) : execQuery.isError ? (
        <ErrorState
          title="Could not load CS metrics"
          description={
            execQuery.error instanceof Error
              ? execQuery.error.message
              : "Request failed"
          }
          onRetry={() => void execQuery.refetch()}
        />
      ) : !data ? (
        <EmptyState
          title="No CS metrics"
          description="Executive renewals/risk payload was empty."
          action={
            <GhostButtonLink href="/v3/companies">
              Browse companies
            </GhostButtonLink>
          }
        />
      ) : null;

    const dashboardBody = !ready ? (
      <LoadingState label="Checking session…" />
    ) : !hasToken ? (
      <PermissionState nextPath="/v3/cs" />
    ) : (
      (gate ?? (
        <div className="space-y-4">
          <MetricCards
            items={[
              {
                label: "Renewals ≤30d",
                value: formatCount(data!.renewals.due_next_30_days),
              },
              {
                label: "Renewals ≤90d",
                value: formatCount(data!.renewals.due_next_90_days),
              },
              {
                label: "Renewal value",
                value: formatCurrencySAR(data!.renewals.total_renewal_value),
              },
              {
                label: "Stalled deals",
                value: formatCount(data!.risk.stalled_deals),
                hint: `${formatCount(data!.risk.inactive_companies)} inactive companies`,
              },
            ]}
          />
          <p className="text-[12px] text-[var(--text-muted)]">
            Portfolio snapshot from{" "}
            <code className="font-mono">GET /api/v1/executive/dashboard</code> —
            not a synthetic health score.
          </p>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                Account sample
              </h3>
              <GhostButtonLink href="/v3/companies">
                All companies
              </GhostButtonLink>
            </div>
            {companiesQuery.isLoading ? (
              <LoadingState label="Loading companies…" />
            ) : companiesQuery.isError ? (
              <p className="text-sm text-[var(--text-muted)]">
                Could not load company sample.
              </p>
            ) : companies.length === 0 ? (
              <EmptyState
                title="No companies"
                description="CS objects attach to company 360 when present."
                action={
                  <GhostButtonLink href="/v3/companies">
                    Open companies
                  </GhostButtonLink>
                }
              />
            ) : (
              <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
                {companies.map((company) => (
                  <li
                    key={company.id}
                    className="border-b border-[var(--border-default)] last:border-b-0"
                  >
                    <Link
                      href={`/v3/companies/${company.id}`}
                      className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus-ring)]"
                    >
                      <span className="min-w-0 truncate font-medium text-[var(--text-primary)]">
                        {companyDisplayName(company)}
                      </span>
                      <span className="shrink-0 text-[12px] capitalize text-[var(--text-muted)]">
                        {company.status?.replace(/_/g, " ") || "—"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ))
    );

    const renewalsBody =
      !ready || !hasToken
        ? dashboardBody
        : (gate ?? (
            <div className="space-y-4">
              <MetricCards
                items={[
                  {
                    label: "Due in 30 days",
                    value: formatCount(data!.renewals.due_next_30_days),
                  },
                  {
                    label: "Due in 90 days",
                    value: formatCount(data!.renewals.due_next_90_days),
                  },
                  {
                    label: "Renewal value",
                    value: formatCurrencySAR(
                      data!.renewals.total_renewal_value,
                    ),
                  },
                  {
                    label: "At-risk listed",
                    value: formatCount(data!.renewals.at_risk?.length ?? 0),
                    hint: "API at_risk array length — not AI risk",
                  },
                ]}
              />
              {(data!.renewals.at_risk?.length ?? 0) > 0 ? (
                <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)] text-sm">
                  {data!.renewals.at_risk.slice(0, 10).map((row, idx) => {
                    const label =
                      typeof row === "object" && row && "name" in row
                        ? String(
                            (row as { name?: unknown }).name ??
                              `Risk ${idx + 1}`,
                          )
                        : `Risk ${idx + 1}`;
                    const companyId =
                      typeof row === "object" && row && "company_id" in row
                        ? String(
                            (row as { company_id?: unknown }).company_id ?? "",
                          )
                        : "";
                    return (
                      <li
                        key={idx}
                        className="border-b border-[var(--border-default)] px-3 py-2.5 last:border-b-0"
                      >
                        {companyId ? (
                          <Link
                            href={`/v3/companies/${companyId}`}
                            className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                          >
                            {label}
                          </Link>
                        ) : (
                          <span className="font-medium text-[var(--text-primary)]">
                            {label}
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="text-sm text-[var(--text-muted)]">
                  No at-risk renewal rows in this response. Counts above still
                  reflect due windows.
                </p>
              )}
              <GhostButtonLink href="/v3/companies">
                Review accounts
              </GhostButtonLink>
            </div>
          ));

    return [
      {
        id: "dashboard",
        label: "CS home",
        audience: "CSMs",
        description:
          "Portfolio renewal/risk snapshot plus a company sample linked to 360.",
        body: dashboardBody,
      },
      {
        id: "onboarding",
        label: "Onboarding",
        audience: "CSMs",
        description: "Implementation milestones and time-to-value trackers.",
        body: (
          <PreviewPanel href="/v3/companies">
            Onboarding milestones are not dual-run yet. Track implementation
            from company 360 when those objects ship.
          </PreviewPanel>
        ),
      },
      {
        id: "health",
        label: "Health score",
        audience: "CS + Leaders",
        description:
          "Account health composition. Scores must cite evidence — never fake AI.",
        body: (
          <PreviewPanel href="/v3/companies">
            No fabricated health scores on this surface. Company 360 may show
            confidence/health when the company API provides it — open an account
            rather than inventing a CS score here.
          </PreviewPanel>
        ),
      },
      {
        id: "renewals",
        label: "Renewals",
        audience: "CSMs",
        description:
          "Upcoming renewals and at-risk list from the executive API.",
        body: renewalsBody,
      },
      {
        id: "expansion",
        label: "Expansion",
        audience: "CS + Sales",
        description:
          "Upsell / cross-sell opportunities linked to company records.",
        body: (
          <PreviewPanel href="/v3/crm" hrefLabel="Open CRM pipeline">
            Expansion opportunities are not a separate CS object yet. Use CRM
            deals linked to companies for upsell coverage.
          </PreviewPanel>
        ),
      },
      {
        id: "qbr",
        label: "QBR",
        audience: "CSMs",
        description: "Quarterly business review prep and follow-ups.",
        body: (
          <PreviewPanel href="/v3/companies">
            QBR prep objects are Preview-only in Design Program IA — no
            fabricated agenda content.
          </PreviewPanel>
        ),
      },
      {
        id: "nps",
        label: "NPS / CSAT",
        audience: "CS Ops",
        description: "Survey responses and trend slices.",
        body: (
          <PreviewPanel>
            Survey APIs are not wired on dual-run CS. Do not invent NPS/CSAT
            numbers for demos.
          </PreviewPanel>
        ),
      },
      {
        id: "plans",
        label: "Success plans",
        audience: "CSMs",
        description: "Success plan objects on company 360 (object model).",
        body: (
          <div className="space-y-3 text-sm text-[var(--text-secondary)]">
            <div className="flex items-center gap-2">
              <PreviewBadge />
              <span className="text-[12px] text-[var(--text-muted)]">
                Object model — not dual-run
              </span>
            </div>
            <p>
              Success plans attach to Companies. Start from a company record
              when CS objects ship; this panel documents IA only.
            </p>
            <GhostButtonLink href="/v3/companies">
              Browse companies
            </GhostButtonLink>
          </div>
        ),
      },
    ];
  }, [
    ready,
    hasToken,
    execQuery,
    data,
    companies,
    companiesQuery.isLoading,
    companiesQuery.isError,
  ]);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <PageHeader
        title="Customer Success"
        description="CS domain — live renewals/risk from executive API; health/NPS stay Preview. No embedded AI insight rail."
        actions={
          <GhostButtonLink href="/v3/companies">Companies</GhostButtonLink>
        }
      />
      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/cs" />
      ) : (
        <DomainWorkbench sections={sections} defaultId="dashboard" />
      )}
    </div>
  );
}
