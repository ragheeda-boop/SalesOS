"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, TrendingUp, Users, Zap, Target, Trophy } from "lucide-react";
import { effectivenessApi, EffectivenessDashboard } from "@/lib/api/effectiveness";
import { effectivenessKeys } from "@/lib/queryKeys";
import { PageHeader } from "../_components/page-header";
import {
  ErrorState,
  LoadingState,
  PermissionState,
} from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";

function Stat({ label, value, icon: Icon }: { label: string; value: string | number; icon: React.ElementType }) {
  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-[var(--text-muted)]" />
        <span className="text-xs font-medium text-[var(--text-muted)]">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-bold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}

function CohortCard({ name, data }: { name: string; data: EffectivenessDashboard["cohorts"][string] }) {
  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold uppercase text-[var(--text-primary)]">{name}</span>
        <span className="text-lg font-bold text-[var(--text-primary)]">{data.total}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-[var(--text-muted)]">
        <div>Action: {data.action_rate}%</div>
        <div>Connection: {data.connection_rate}%</div>
        <div>Meeting: {data.meeting_rate}%</div>
        <div>Win: {data.win_rate}%</div>
      </div>
      {data.lift_meeting > 0 && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          <TrendingUp className="h-3 w-3 text-[var(--text-muted)]" />
          <span className="text-[var(--text-primary)] font-medium">{data.lift_meeting}x lift</span>
        </div>
      )}
    </div>
  );
}

function LiftPanel({ lift }: { lift: EffectivenessDashboard["lift"] }) {
  const meetingLift = lift.meeting_lift;
  const isNumerator = meetingLift.value !== null;
  const pct = isNumerator ? ((meetingLift.value! - 1) * 100).toFixed(0) : null;

  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-6">
      <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
        <TrendingUp className="h-4 w-4" /> SalesOS Lift vs Baseline
      </h3>
      <div className="mt-4 grid grid-cols-2 gap-6">
        <div>
          <p className="text-xs text-[var(--text-muted)] mb-1">Elevated (critical + high)</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{lift.elevated_total} accounts</p>
          <p className="text-sm text-[var(--text-muted)]">{lift.elevated_meetings} meetings / {lift.elevated_connections} connections</p>
        </div>
        <div>
          <p className="text-xs text-[var(--text-muted)] mb-1">Baseline (medium + low)</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{lift.baseline_total} accounts</p>
          <p className="text-sm text-[var(--text-muted)]">{lift.baseline_meetings} meetings / {lift.baseline_connections} connections</p>
        </div>
      </div>
      <div className="mt-4 p-3 rounded-md bg-[var(--bg-secondary)]">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-[var(--text-primary)]">Meeting Lift</span>
          {isNumerator ? (
            <span className={`text-lg font-bold ${meetingLift.value! >= 1 ? "text-[var(--text-primary)]" : "text-[var(--text-muted)]"}`}>
              {meetingLift.display}
            </span>
          ) : (
            <span className="text-lg font-bold text-[var(--text-muted)]">N/A</span>
          )}
        </div>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          {isNumerator
            ? (pct && parseFloat(pct) >= 0 ? `+${pct}% more meetings per account` : `${pct}% fewer meetings per account`)
            : "Baseline rate = 0% — comparison not computable"}
        </p>
      </div>
      <div className="mt-2 p-3 rounded-md bg-[var(--bg-secondary)]">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-[var(--text-primary)]">Connection Lift</span>
          {lift.connection_lift.value !== null ? (
            <span className="text-lg font-bold text-[var(--text-primary)]">{lift.connection_lift.display}</span>
          ) : (
            <span className="text-lg font-bold text-[var(--text-muted)]">N/A</span>
          )}
        </div>
      </div>
    </div>
  );
}

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-right text-[var(--text-muted)] truncate">{label}</span>
      <div className="flex-1 h-4 bg-[var(--bg-secondary)] rounded overflow-hidden">
        <div className="h-full bg-[var(--border-primary)] rounded" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-[var(--text-muted)]">{value}</span>
    </div>
  );
}

const EMPTY_COHORT = {
  total: 0,
  action_rate: 0,
  connection_rate: 0,
  meeting_rate: 0,
  win_rate: 0,
  revenue: 0,
  lift_meeting: 0,
};

export default function EffectivenessPage() {
  const { ready, hasToken } = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: effectivenessKeys.dashboard(),
    queryFn: () => effectivenessApi.getDashboard(),
    refetchInterval: 30_000,
    enabled: ready && hasToken,
  });

  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;
  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/effectiveness" />;
  if (isLoading) return <LoadingState label="Loading effectiveness data…" />;
  if (isError)
    return (
      <div className="mx-auto max-w-7xl">
        <PageHeader
          title="Business Effectiveness"
          description="SalesOS-driven pipeline performance"
        />
        <ErrorState
          title="Could not load effectiveness data"
          description={error instanceof Error ? error.message : "Request failed"}
          onRetry={() => void refetch()}
        />
      </div>
    );

  const d: EffectivenessDashboard | undefined = data as EffectivenessDashboard | undefined;
  const cohorts = {
    critical: d?.cohorts.critical ?? EMPTY_COHORT,
    high: d?.cohorts.high ?? EMPTY_COHORT,
    medium: d?.cohorts.medium ?? EMPTY_COHORT,
    low: d?.cohorts.low ?? EMPTY_COHORT,
  };
  const byLevelEntries = Object.entries(d?.by_level ?? {});
  const bySellerEntries = Object.entries(d?.by_seller ?? {});
  const maxLevelAccounts = Math.max(...byLevelEntries.map(([, v]) => v.count), 1);
  const maxAccounts = Math.max(...bySellerEntries.map(([, s]) => s.count), 1);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Business Effectiveness"
        description="SalesOS-driven pipeline performance"
      />

      {/* Summary KPIs */}
      {d && (
        <div className="grid grid-cols-4 gap-4">
          <Stat label="Total Accounts" value={d.summary.total_accounts} icon={Users} />
          <Stat label="Meetings" value={d.summary.meetings} icon={Target} />
          <Stat label="Won" value={d.summary.won} icon={Trophy} />
          <Stat label="Revenue" value={`$${d.summary.revenue.toLocaleString()}`} icon={BarChart3} />
        </div>
      )}

      {/* Rates */}
      {d && (
        <div className="grid grid-cols-4 gap-4">
          <Stat label="Action Rate" value={`${d.rates.action_rate}%`} icon={Zap} />
          <Stat label="Connection Rate" value={`${d.rates.connection_rate}%`} icon={Users} />
          <Stat label="Meeting Rate" value={`${d.rates.meeting_rate}%`} icon={Target} />
          <Stat label="Win Rate" value={`${d.rates.win_rate}%`} icon={Trophy} />
        </div>
      )}

      {/* Cohorts + Lift */}
      {d && (
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-3 grid grid-cols-2 gap-4">
            <CohortCard name="critical" data={cohorts.critical} />
            <CohortCard name="high" data={cohorts.high} />
            <CohortCard name="medium" data={cohorts.medium} />
            <CohortCard name="low" data={cohorts.low} />
          </div>
          <div className="col-span-2">
            <LiftPanel lift={d.lift} />
          </div>
        </div>
      )}

      {/* By Level + By Seller */}
      {d && (
        <div className="grid grid-cols-2 gap-6">
          <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">By Intent Level</h3>
            {byLevelEntries.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">No intent-level data yet.</p>
            ) : (
              <div className="space-y-2">
                {byLevelEntries.map(([level, v]) => (
                  <Bar key={level} label={level} value={v.count} max={maxLevelAccounts} />
                ))}
              </div>
            )}
          </div>
          <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">By Seller</h3>
            {bySellerEntries.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">No seller data yet.</p>
            ) : (
              <div className="space-y-2">
                {bySellerEntries.map(([seller, v]) => (
                  <Bar key={seller} label={seller} value={v.count} max={maxAccounts} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* NBA Stats */}
      {d && d.nba.total_actions > 0 && (
        <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <Zap className="h-4 w-4" /> NBA Effectiveness
          </h3>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div><span className="text-[var(--text-muted)]">Total Actions:</span> <span className="font-bold text-[var(--text-primary)]">{d.nba.total_actions}</span></div>
            <div><span className="text-[var(--text-muted)]">Accepted:</span> <span className="font-bold text-[var(--text-primary)]">{d.nba.acceptance_rate}%</span></div>
            <div><span className="text-[var(--text-muted)]">Modified:</span> <span className="font-bold text-[var(--text-primary)]">{d.nba.modification_rate}%</span></div>
            <div><span className="text-[var(--text-muted)]">Rejected:</span> <span className="font-bold text-[var(--text-primary)]">{d.nba.rejection_rate}%</span></div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && d && d.summary.total_accounts === 0 && (
        <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-12 text-center">
          <BarChart3 className="h-10 w-10 text-[var(--text-muted)] mx-auto mb-4" />
          <p className="text-[var(--text-muted)]">No effectiveness data yet. Accounts need funnel events to appear here.</p>
        </div>
      )}
    </div>
  );
}
