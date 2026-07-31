"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { getExecutiveDashboard, listOpportunities } from "@/lib/api";
import { dashboardKeys, opportunityKeys } from "@/lib/queryKeys";
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
import {
  formatCount,
  formatCurrencySAR,
  formatPercent,
  stageLabel,
} from "../_components/format";
import { useAccessToken } from "../_hooks/useAccessToken";

function PreviewPanel({
  children,
  legacyHref,
  legacyLabel = "Open legacy analytics",
}: {
  children: ReactNode;
  legacyHref?: string;
  legacyLabel?: string;
}) {
  return (
    <div className="space-y-3 text-sm text-[var(--text-secondary)]">
      <div className="flex items-center gap-2">
        <PreviewBadge />
        <span className="text-[12px] text-[var(--text-muted)]">
          Not wired — no invented metrics
        </span>
      </div>
      <p>{children}</p>
      {legacyHref ? (
        <GhostButtonLink href={legacyHref}>{legacyLabel}</GhostButtonLink>
      ) : null}
    </div>
  );
}

export default function V3AnalyticsPage() {
  const { ready, hasToken } = useAccessToken();

  const execQuery = useQuery({
    queryKey: dashboardKeys.exec(),
    queryFn: () => getExecutiveDashboard(getTenantId()),
    enabled: ready && hasToken,
    staleTime: 60_000,
  });

  const oppQuery = useQuery({
    queryKey: opportunityKeys.list(),
    queryFn: () => listOpportunities(getTenantId()),
    enabled: ready && hasToken,
    staleTime: 15_000,
  });

  const data = execQuery.data;
  const deals = useMemo(() => {
    const items = oppQuery.data?.items ?? [];
    return [...items]
      .sort((a, b) => (b.value || 0) - (a.value || 0))
      .slice(0, 8);
  }, [oppQuery.data?.items]);

  const sections: DomainSection[] = useMemo(() => {
    const loading =
      !ready || !hasToken || execQuery.isLoading ? (
        <LoadingState label="Loading executive metrics…" />
      ) : execQuery.isError ? (
        <ErrorState
          title="Could not load analytics"
          description={
            execQuery.error instanceof Error
              ? execQuery.error.message
              : "Request failed"
          }
          onRetry={() => void execQuery.refetch()}
        />
      ) : !data ? (
        <EmptyState
          title="No analytics data"
          description="Executive dashboard returned empty. Legacy analytics may still have charts."
          action={
            <GhostButtonLink href="/analytics">
              Open legacy analytics
            </GhostButtonLink>
          }
        />
      ) : null;

    const revenueBody = loading ?? (
      <div className="space-y-4">
        <MetricCards
          items={[
            {
              label: "Booked revenue",
              value: formatCurrencySAR(data!.revenue.total_booked),
              hint: `${data!.revenue.growth_percent >= 0 ? "+" : ""}${data!.revenue.growth_percent}% growth`,
            },
            {
              label: "Total pipeline",
              value: formatCurrencySAR(data!.revenue.total_pipeline),
            },
            {
              label: "Weighted pipeline",
              value: formatCurrencySAR(data!.revenue.weighted_pipeline),
            },
            {
              label: "Forecast field",
              value: formatCurrencySAR(data!.revenue.forecast),
              hint: "From executive API — not a commit model",
            },
          ]}
        />
        <p className="text-[12px] text-[var(--text-muted)]">
          Source:{" "}
          <code className="font-mono">GET /api/v1/executive/dashboard</code> ·
          revenue
        </p>
        <GhostButtonLink href="/v3/crm">Open CRM pipeline</GhostButtonLink>
      </div>
    );

    const pipelineBody = loading ?? (
      <div className="space-y-4">
        <MetricCards
          items={[
            {
              label: "Open deals",
              value: formatCount(data!.pipeline.total_deals),
            },
            {
              label: "Pipeline value",
              value: formatCurrencySAR(data!.pipeline.total_value),
            },
            {
              label: "Win rate",
              value: formatPercent(data!.pipeline.win_rate, { ratio: true }),
            },
            {
              label: "Avg deal size",
              value: formatCurrencySAR(data!.pipeline.avg_deal_size),
            },
          ]}
        />
        {data!.pipeline.by_stage.length > 0 ? (
          <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
                <tr>
                  <th scope="col" className="px-3 py-2 font-medium">
                    Stage
                  </th>
                  <th scope="col" className="px-3 py-2 font-medium">
                    Deals
                  </th>
                  <th scope="col" className="px-3 py-2 font-medium">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {data!.pipeline.by_stage.map((row) => (
                  <tr
                    key={row.stage}
                    className="border-b border-[var(--border-default)] last:border-b-0"
                  >
                    <td className="px-3 py-2 capitalize text-[var(--text-primary)]">
                      {stageLabel(row.stage)}
                    </td>
                    <td className="px-3 py-2 tabular-nums text-[var(--text-secondary)]">
                      {formatCount(row.cnt)}
                    </td>
                    <td className="px-3 py-2 tabular-nums text-[var(--text-secondary)]">
                      {formatCurrencySAR(row.val)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            No stage breakdown in this response.
          </p>
        )}

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-medium text-[var(--text-primary)]">
              Largest open deals
            </h3>
            <GhostButtonLink href="/v3/crm">All deals</GhostButtonLink>
          </div>
          {oppQuery.isLoading ? (
            <LoadingState label="Loading deals…" />
          ) : oppQuery.isError ? (
            <p className="text-sm text-[var(--text-muted)]">
              Could not load opportunity list.
            </p>
          ) : deals.length === 0 ? (
            <EmptyState
              title="No deals yet"
              description="Create opportunities from a company record."
              action={
                <GhostButtonLink href="/v3/companies">
                  Browse companies
                </GhostButtonLink>
              }
            />
          ) : (
            <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
              {deals.map((opp) => (
                <li
                  key={opp.id}
                  className="flex items-center justify-between gap-3 border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
                >
                  <span className="min-w-0">
                    <Link
                      href={`/v3/crm/${opp.id}`}
                      className="block truncate font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {opp.name}
                    </Link>
                    <span className="mt-0.5 block truncate text-[12px] text-[var(--text-muted)]">
                      {opp.company_id ? (
                        <Link
                          href={`/v3/companies/${opp.company_id}`}
                          className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                        >
                          {opp.company_name || "Company"}
                        </Link>
                      ) : (
                        opp.company_name || "—"
                      )}
                      {" · "}
                      <span className="capitalize">
                        {stageLabel(opp.stage)}
                      </span>
                    </span>
                  </span>
                  <span className="shrink-0 tabular-nums text-[var(--text-secondary)]">
                    {formatCurrencySAR(opp.value)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );

    const performanceBody = loading ?? (
      <div className="space-y-4">
        <MetricCards
          items={[
            {
              label: "Active team",
              value: formatCount(data!.team.active_employees),
              hint: `${formatCount(data!.team.total_employees)} total employees`,
            },
            {
              label: "Avg win rate",
              value: formatPercent(data!.team.avg_win_rate, { ratio: true }),
            },
            {
              label: "Won deals",
              value: formatCount(data!.pipeline.won_deals),
            },
            {
              label: "Lost deals",
              value: formatCount(data!.pipeline.lost_deals),
            },
          ]}
        />
        <GhostButtonLink href="/v3/people">Browse people</GhostButtonLink>
      </div>
    );

    const activityBody = loading ?? (
      <div className="space-y-4">
        <MetricCards
          items={[
            {
              label: "New companies (30d)",
              value: formatCount(data!.growth.new_companies_30d),
            },
            {
              label: "New contacts (30d)",
              value: formatCount(data!.growth.new_contacts_30d),
            },
            {
              label: "New opportunities (30d)",
              value: formatCount(data!.growth.new_opportunities_30d),
            },
            {
              label: "New contracts (30d)",
              value: formatCount(data!.growth.new_contracts_30d),
            },
          ]}
        />
        <p className="text-[12px] text-[var(--text-muted)]">
          Growth counters from the executive dashboard — not a full activity
          timeline.
        </p>
      </div>
    );

    const customerBody = loading ?? (
      <div className="space-y-4">
        <MetricCards
          items={[
            {
              label: "Stalled deals",
              value: formatCount(data!.risk.stalled_deals),
            },
            {
              label: "Expiring contracts",
              value: formatCount(data!.risk.expiring_contracts),
            },
            {
              label: "Inactive companies",
              value: formatCount(data!.risk.inactive_companies),
            },
            {
              label: "Low-pipeline people",
              value: formatCount(data!.risk.low_pipeline_employees),
            },
          ]}
        />
        <div className="flex flex-wrap gap-2">
          <GhostButtonLink href="/v3/cs">CS workbench</GhostButtonLink>
          <GhostButtonLink href="/v3/companies">Companies</GhostButtonLink>
        </div>
      </div>
    );

    const retentionBody = loading ?? (
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
              label: "At-risk listed",
              value: formatCount(data!.renewals.at_risk?.length ?? 0),
              hint: "Count of at_risk entries from API",
            },
          ]}
        />
        <GhostButtonLink href="/v3/cs">Open CS renewals</GhostButtonLink>
      </div>
    );

    return [
      {
        id: "revenue",
        label: "Revenue",
        audience: "Leaders",
        description:
          "Booked revenue, growth, and pipeline totals from the executive API.",
        body: revenueBody,
      },
      {
        id: "pipeline",
        label: "Pipeline",
        audience: "Sales",
        description:
          "Stage distribution, deal totals, and largest open opportunities.",
        body: pipelineBody,
      },
      {
        id: "forecast",
        label: "Forecast",
        audience: "Managers",
        description:
          "Commit / best-case views — requires forecast models, not invented scores.",
        body: (
          <PreviewPanel legacyHref="/analytics">
            Forecast commit models are not exposed as a dedicated dual-run
            surface yet. The revenue section shows the executive{" "}
            <code className="font-mono text-[12px]">forecast</code> field only —
            treat it as a stored number, not a governance commit.
          </PreviewPanel>
        ),
      },
      {
        id: "performance",
        label: "Sales performance",
        audience: "Managers",
        description:
          "Team size, win/loss, and average win rate from executive metrics.",
        body: performanceBody,
      },
      {
        id: "activity",
        label: "Activity",
        audience: "Ops",
        description:
          "30-day growth counters (companies, contacts, opportunities, contracts).",
        body: activityBody,
      },
      {
        id: "customer",
        label: "Customer",
        audience: "CS + Sales",
        description:
          "Risk signals: stalled deals, expiries, inactive accounts.",
        body: customerBody,
      },
      {
        id: "retention",
        label: "Retention",
        audience: "CS",
        description:
          "Renewal windows and renewal value from the executive dashboard.",
        body: retentionBody,
      },
      {
        id: "custom",
        label: "Custom reports",
        audience: "Analysts",
        description: "Analytics Studio on Data Grid + charts (engine TBD).",
        body: (
          <PreviewPanel legacyHref="/analytics">
            Custom report builder is not wired in this spike. Use structured
            sections for IA; do not treat empty panels as live AI insights.
          </PreviewPanel>
        ),
      },
    ];
  }, [
    ready,
    hasToken,
    execQuery,
    data,
    oppQuery.isLoading,
    oppQuery.isError,
    deals,
  ]);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <PageHeader
        title="Analytics"
        description="Reporting IA with live executive metrics where the API exists. Ask AI stays in the topbar popup."
        actions={
          <div className="flex flex-wrap gap-2">
            <GhostButtonLink href="/v3/crm">View pipeline</GhostButtonLink>
            <GhostButtonLink href="/analytics">
              Legacy analytics
            </GhostButtonLink>
          </div>
        }
      />

      {!ready ? (
        <LoadingState label="Checking session…" />
      ) : !hasToken ? (
        <PermissionState nextPath="/v3/analytics" />
      ) : (
        <DomainWorkbench sections={sections} defaultId="pipeline" />
      )}
    </div>
  );
}
