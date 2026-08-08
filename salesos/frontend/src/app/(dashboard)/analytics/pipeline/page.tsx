"use client";
/* eslint-disable custom-rules/no-hardcoded-colors */

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { BarChart, LineChart, PieChart, MetricCard } from "@salesos/charts";
import { ExportShareBar } from "@/components/analytics";
import { normalizePipelineAnalytics, type PipelineAnalyticsView } from "@/lib/pipelineAnalytics";
import { ArrowLeft, Clock, DollarSign, Target, BarChart3, RefreshCw } from "lucide-react";

const STAGE_COLORS: Record<string, string> = {
  lead: "#3B82F6",
  opportunity: "#6366F1",
  proposal: "#F59E0B",
  negotiation: "#F97316",
  closed_won: "#10B981",
  closed_lost: "#EF4444",
};

const STAGE_LABELS: Record<string, string> = {
  lead: "Lead",
  opportunity: "Opportunity",
  proposal: "Proposal",
  negotiation: "Negotiation",
  closed_won: "Closed Won",
  closed_lost: "Closed Lost",
};

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

function formatCurrency(value: number): string {
  const n = Number.isFinite(value) ? value : 0;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M SAR`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K SAR`;
  return `${n.toLocaleString()} SAR`;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-[var(--bg-tertiary)]" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 rounded-xl bg-[var(--bg-tertiary)]" />
        <div className="h-64 rounded-xl bg-[var(--bg-tertiary)]" />
      </div>
    </div>
  );
}

export default function PipelineAnalyticsOverviewPage() {
  const [analytics, setAnalytics] = useState<PipelineAnalyticsView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/api/v1/pipeline/analytics");
      setAnalytics(normalizePipelineAnalytics(res.data));
    } catch {
      setError("Failed to load pipeline analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-sm text-[var(--status-danger-text)] mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition"
        >
          <RefreshCw className="h-4 w-4" /> Retry
        </button>
      </div>
    );
  }

  if (!analytics) return null;

  const funnel = analytics.conversion_funnel;
  const velocity = analytics.velocity;
  const stageDuration = analytics.stage_duration;
  const valueOverTime = analytics.value_over_time;

  const velocityData = velocity.map((v) => ({
    label: STAGE_LABELS[v.stage] || v.stage,
    value: v.avg_days,
  }));

  const wonCount = analytics.total_won;
  const lostCount = analytics.total_lost;
  const wonLostData =
    wonCount + lostCount > 0
      ? [
          { label: "Won", value: wonCount, color: "#10B981" },
          { label: "Lost", value: lostCount, color: "#EF4444" },
        ]
      : [
          {
            label: "Won",
            value: Math.round(analytics.total_pipeline * (analytics.win_rate / 100)),
            color: "#10B981",
          },
          {
            label: "Lost",
            value: Math.round(analytics.total_pipeline * (1 - analytics.win_rate / 100)),
            color: "#EF4444",
          },
        ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/analytics"
            className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Pipeline Analytics</h1>
            <p className="text-sm text-[var(--text-muted)]">
              Conversion, velocity, and pipeline health
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-[var(--border-default)] overflow-hidden">
            {DATE_RANGES.map((r) => (
              <button
                key={r.days}
                onClick={() => setDateRange(r.days as 7 | 30 | 90)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition",
                  dateRange === r.days
                    ? "bg-[var(--muhide-orange)] text-white"
                    : "bg-[var(--bg-primary)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <ExportShareBar reportName="Pipeline Analytics" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Pipeline"
          value={formatCurrency(analytics.total_pipeline)}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <MetricCard
          label="Win Rate"
          value={`${analytics.win_rate}%`}
          icon={<Target className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Deal Size"
          value={formatCurrency(analytics.avg_deal_size)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Cycle Time"
          value={`${analytics.avg_cycle_days}d`}
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Conversion Funnel
          </h3>
          {funnel.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] py-8 text-center">
              No conversion data for this tenant yet
            </p>
          ) : (
            <div className="space-y-1.5">
              {funnel.map((item) => {
                const maxCount = Math.max(...funnel.map((f) => f.count), 1);
                const pct = (item.count / maxCount) * 100;
                const color = STAGE_COLORS[item.stage] || "#6B7280";
                return (
                  <div key={item.stage} className="flex items-center gap-3">
                    <span className="min-w-[100px] text-xs text-[var(--text-muted)]">
                      {STAGE_LABELS[item.stage] || item.stage}
                    </span>
                    <div className="flex-1 h-7 rounded-lg bg-[var(--bg-tertiary)] overflow-hidden relative">
                      <div
                        className="h-full rounded-lg transition-all duration-500 flex items-center px-2"
                        style={{
                          width: `${Math.max(pct, 5)}%`,
                          backgroundColor: color,
                        }}
                      >
                        <span className="text-[10px] font-medium text-white whitespace-nowrap">
                          {item.count}
                        </span>
                      </div>
                    </div>
                    <span className="min-w-[70px] text-right text-[10px] text-[var(--text-muted)]">
                      {formatCurrency(item.value)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          {analytics.conversion_rate_lead_to_close > 0 && (
            <div className="mt-3 text-center">
              <span className="text-xs text-[var(--text-muted)]">
                Lead → Close Conversion:{" "}
                <span className="font-semibold text-[var(--muhide-orange)]">
                  {analytics.conversion_rate_lead_to_close}%
                </span>
              </span>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Velocity (Avg Days per Stage)
          </h3>
          {velocityData.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] py-8 text-center">
              No velocity data for this tenant yet
            </p>
          ) : (
            <BarChart data={velocityData} height={250} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Pipeline Value Over Time
          </h3>
          {valueOverTime.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] py-8 text-center">
              No pipeline value history yet
            </p>
          ) : (
            <LineChart
              series={[
                {
                  name: "Pipeline Value",
                  color: "#F57C1E",
                  data: valueOverTime.map((v) => v.value),
                },
              ]}
              height={250}
            />
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Win/Loss Distribution
          </h3>
          <PieChart data={wonLostData} height={200} />
        </div>
      </div>

      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
          Stage Duration Breakdown
        </h3>
        <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Stage
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Median (p50)
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  p95
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Distribution
                </th>
              </tr>
            </thead>
            <tbody>
              {stageDuration.map((item) => (
                <tr
                  key={item.stage}
                  className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2">
                    <span className="flex items-center gap-1.5">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{
                          backgroundColor: STAGE_COLORS[item.stage] || "#6B7280",
                        }}
                      />
                      <span className="text-[var(--text-primary)]">
                        {STAGE_LABELS[item.stage] || item.stage}
                      </span>
                    </span>
                  </td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">{item.p50}d</td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">{item.p95}d</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 flex-1 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min((item.p50 / Math.max(item.p95, 1)) * 100, 100)}%`,
                            backgroundColor: STAGE_COLORS[item.stage] || "#6B7280",
                          }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
              {stageDuration.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-3 py-6 text-center text-xs text-[var(--text-muted)]"
                  >
                    No stage duration data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
