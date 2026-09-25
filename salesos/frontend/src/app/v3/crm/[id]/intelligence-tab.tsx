"use client";

import { useQuery } from "@tanstack/react-query";
import { getDealIntelligence } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { ErrorState, LoadingState } from "../../_components/states";

function label(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function DealIntelligenceTab({ opportunityId }: { opportunityId: string }) {
  const tenantId = getTenantId();
  const query = useQuery({
    queryKey: ["dealIntelligence", opportunityId],
    queryFn: () => getDealIntelligence(opportunityId, tenantId),
    enabled: Boolean(opportunityId && tenantId),
    staleTime: 30_000,
  });

  if (query.isLoading) return <LoadingState label="Loading deal intelligence…" />;
  if (query.isError) {
    return (
      <ErrorState
        title="Could not load deal intelligence"
        description={query.error instanceof Error ? query.error.message : "Request failed"}
        onRetry={() => void query.refetch()}
      />
    );
  }
  if (!query.data) return null;

  const data = query.data;
  return (
    <div className="space-y-4" data-testid="deal-intelligence">
      <div className="rounded-lg border border-[var(--border-default)] p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
          Rule-based CRM health
        </p>
        <h2 className="mt-1 text-lg font-semibold text-[var(--text-primary)]">
          {data.health_score == null ? "Insufficient CRM data" : `${label(data.health_level)} · ${Math.round(data.health_score * 100)}%`}
        </h2>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-xs text-[var(--text-muted)]">Stage</dt><dd>{label(data.stage) || "—"}</dd></div>
          <div><dt className="text-xs text-[var(--text-muted)]">Probability</dt><dd>{data.probability == null ? "Missing" : `${Math.round(data.probability * 100)}%`}</dd></div>
          <div><dt className="text-xs text-[var(--text-muted)]">Days in stage</dt><dd>{data.days_in_stage == null ? "Not recorded" : Math.floor(data.days_in_stage)}</dd></div>
          <div><dt className="text-xs text-[var(--text-muted)]">Recorded activities</dt><dd>{data.activity_count}</dd></div>
        </dl>
      </div>

      {data.missing_fields.length > 0 ? (
        <p className="rounded-md bg-[var(--bg-secondary)] p-3 text-sm text-[var(--text-secondary)]">
          Missing CRM inputs: {data.missing_fields.map(label).join(", ")}.
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <section className="space-y-2" aria-labelledby="deal-intelligence-risks">
          <h3 id="deal-intelligence-risks" className="text-sm font-medium text-[var(--text-primary)]">Risks</h3>
          {data.risk_factors.length ? (
            <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--text-secondary)]">
              {data.risk_factors.map((factor) => <li key={factor}>{factor}</li>)}
            </ul>
          ) : <p className="text-sm text-[var(--text-muted)]">No rule-based risks from the available fields.</p>}
        </section>
        <section className="space-y-2" aria-labelledby="deal-intelligence-opportunities">
          <h3 id="deal-intelligence-opportunities" className="text-sm font-medium text-[var(--text-primary)]">Positive signals</h3>
          {data.opportunity_factors.length ? (
            <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--text-secondary)]">
              {data.opportunity_factors.map((factor) => <li key={factor}>{factor}</li>)}
            </ul>
          ) : <p className="text-sm text-[var(--text-muted)]">No positive rule matches from the available fields.</p>}
        </section>
      </div>

      <p className="text-xs text-[var(--text-muted)]">
        Calculated from this tenant&apos;s opportunity, stage history, and activity records at {new Date(data.generated_at).toLocaleString()}. This is an explainable rule summary, not a calibrated sales prediction or an automatic CRM update.
      </p>
    </div>
  );
}
