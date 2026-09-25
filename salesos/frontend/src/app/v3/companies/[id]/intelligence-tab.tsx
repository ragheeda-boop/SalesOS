"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Button, useToast } from "@salesos/ui";
import { getCompanyAccountIntelligence, recordCompanyAccountEvidence } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { ErrorState, EmptyState, LoadingState } from "../../_components/states";

const labels: Record<string, string> = {
  opportunity_history: "No opportunities are linked to this company yet.",
  activity_history: "No company activity is recorded yet.",
};

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border-default)] p-3">
      <dt className="text-xs text-[var(--text-muted)]">{label}</dt>
      <dd className="mt-1 text-xl font-semibold text-[var(--text-primary)]">{value}</dd>
    </div>
  );
}

function formatActivityDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Riyadh",
  }).format(date);
}

export function IntelligenceTab({ companyId }: { companyId: string }) {
  const tenantId = getTenantId();
  const { toast } = useToast();
  const evidenceMutation = useMutation({
    mutationFn: () => recordCompanyAccountEvidence(companyId, tenantId),
    onSuccess: (result) => {
      toast({
        title: result.created ? "Evidence snapshot recorded" : "Evidence already up to date",
        description: `${result.evidence_count} evidence items · ${result.confidence_level} confidence`,
        variant: "success",
      });
    },
    onError: (error) => {
      toast({
        title: "Could not record evidence",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "error",
      });
    },
  });
  const query = useQuery({
    queryKey: ["company-account-intelligence", tenantId, companyId],
    queryFn: () => getCompanyAccountIntelligence(companyId, tenantId),
    enabled: Boolean(tenantId && companyId),
  });

  if (query.isLoading) return <LoadingState label="Loading CRM account facts…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load account facts"
        description={query.error instanceof Error ? query.error.message : "Request failed"}
        onRetry={() => void query.refetch()}
      />
    );
  }
  if (!query.data) {
    return (
      <EmptyState
        title="No account data available"
        description="The CRM did not return an account summary for this company."
      />
    );
  }

  const data = query.data;
  const missingMessages = data.missing_data.map((item) => labels[item] ?? item);

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">CRM account facts</h2>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {data.company_name}
              {[data.industry, data.city].filter(Boolean).length > 0
                ? ` · ${[data.industry, data.city].filter(Boolean).join(" · ")}`
                : ""}
            </p>
          </div>
          <span className="rounded-full bg-[var(--bg-secondary)] px-2.5 py-1 text-xs capitalize text-[var(--text-secondary)]">
            {data.company_status || "status unavailable"}
          </span>
        </div>

        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Metric label="Opportunities" value={data.total_opportunities} />
          <Metric label="Open opportunities" value={data.active_opportunities} />
          <Metric label="Won deals" value={data.won_deals} />
          <Metric label="Lost deals" value={data.lost_deals} />
          <Metric label="Recorded activities" value={data.activity_count} />
          <Metric
            label="Days since last activity"
            value={data.days_since_activity == null ? "—" : data.days_since_activity}
          />
        </dl>

        <dl className="mt-4 grid gap-3 border-t border-[var(--border-default)] pt-3 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-[var(--text-muted)]">Last recorded activity</dt>
            <dd className="mt-1 text-sm text-[var(--text-primary)]">
              {formatActivityDate(data.last_activity_at)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-[var(--text-muted)]">Data source</dt>
            <dd className="mt-1 text-sm text-[var(--text-primary)]">
              Tenant CRM opportunities and company activity records
            </dd>
          </div>
        </dl>
      </section>

      <section
        aria-label="Account signals"
        className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
        data-testid="account-signals"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Account signals</h3>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[var(--bg-secondary)] px-2.5 py-1 text-xs text-[var(--text-secondary)]">
              {data.account_signals.status.replaceAll("_", " ")}
            </span>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={evidenceMutation.isPending}
              onClick={() => evidenceMutation.mutate()}
              data-testid="record-account-evidence"
            >
              {evidenceMutation.isPending ? "Recording…" : "Record evidence snapshot"}
            </Button>
          </div>
        </div>
        {evidenceMutation.data && (
          <p role="status" className="mt-2 text-xs text-[var(--text-secondary)]">
            {evidenceMutation.data.created
              ? "Evidence snapshot recorded."
              : "Evidence is already up to date."}{" "}
            {evidenceMutation.data.evidence_count} source-linked evidence items.
          </p>
        )}
        {data.account_signals.signals.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {data.account_signals.signals.map((signal) => (
              <li key={signal.code} className="rounded border border-[var(--border-default)] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    {signal.title}
                  </span>
                  <span className="text-xs capitalize text-[var(--text-muted)]">
                    {signal.polarity} · {signal.source}
                  </span>
                </div>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">{signal.detail}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-[var(--text-secondary)]">No current attention signal.</p>
        )}
        {data.account_signals.recommendations.length > 0 && (
          <div className="mt-3 border-t border-[var(--border-default)] pt-3">
            <h4 className="text-xs font-medium text-[var(--text-muted)]">Suggested next actions</h4>
            <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-[var(--text-secondary)]">
              {data.account_signals.recommendations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        )}
      </section>

      <section
        aria-label="Engagement trend"
        className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
        data-testid="engagement-trend"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">CRM activity trend</h3>
          <span className="rounded-full bg-[var(--bg-secondary)] px-2.5 py-1 text-xs capitalize text-[var(--text-secondary)]">
            {data.engagement_trend.trend.replaceAll("_", " ")}
          </span>
        </div>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Recent 90 days: {data.engagement_trend.recent_90_days} activities · Previous 90 days: {data.engagement_trend.previous_90_days} activities
          {data.engagement_trend.change_percent == null
            ? " · percentage change unavailable"
            : ` · ${data.engagement_trend.change_percent > 0 ? "+" : ""}${data.engagement_trend.change_percent}%`}
        </p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">{data.engagement_trend.interpretation}</p>
      </section>

      {missingMessages.length > 0 && (
        <section
          aria-label="Missing account data"
          className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
        >
          <h3 className="text-sm font-medium text-[var(--text-primary)]">Data gaps</h3>
          <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-[var(--text-secondary)]">
            {missingMessages.map((message) => <li key={message}>{message}</li>)}
          </ul>
        </section>
      )}

      <p className="text-xs text-[var(--text-muted)]">
        Signals are deterministic rules over persisted CRM records, with source tables shown. No predictive score is calculated and no CRM data is changed.
      </p>
    </div>
  );
}
