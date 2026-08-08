"use client";
/* eslint-disable custom-rules/no-hardcoded-colors */

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { BarChart, LineChart, MetricCard } from "@salesos/charts";
import { normalizePipelineAnalytics, type PipelineAnalyticsView } from "@/lib/pipelineAnalytics";
import { ArrowLeft, Clock, DollarSign, Target, BarChart3 } from "lucide-react";

function formatCurrency(value: number): string {
  const n = Number.isFinite(value) ? value : 0;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M SAR`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K SAR`;
  return `${n.toLocaleString()} SAR`;
}

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

function FunnelChart({ data }: { data: { stage: string; count: number; value: number }[] }) {
  if (data.length === 0) {
    return (
      <p className="text-xs text-[var(--text-muted)] py-8 text-center">
        No conversion data for this tenant yet
      </p>
    );
  }
  const maxCount = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">Conversion Funnel</h3>
      <div className="space-y-1.5">
        {data.map((item) => {
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
    </div>
  );
}

function VelocityChart({ data }: { data: { stage: string; avg_days: number }[] }) {
  if (data.length === 0) {
    return (
      <p className="text-xs text-[var(--text-muted)] py-8 text-center">
        No velocity data for this tenant yet
      </p>
    );
  }
  const chartData = data.map((d) => ({
    label: STAGE_LABELS[d.stage] || d.stage,
    value: d.avg_days,
    color: STAGE_COLORS[d.stage] || "#6B7280",
  }));
  return <BarChart data={chartData} title="Average Days per Stage (Velocity)" height={220} />;
}

function StageDurationTable({ data }: { data: { stage: string; p50: number; p95: number }[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">Stage Duration Breakdown</h3>
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
            {data.map((item) => (
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
            {data.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-xs text-[var(--text-muted)]">
                  No stage duration data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function PipelineAnalyticsPage() {
  const [analytics, setAnalytics] = useState<PipelineAnalyticsView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/api/v1/pipeline/analytics");
        setAnalytics(normalizePipelineAnalytics(res.data));
      } catch {
        setError("Failed to load pipeline analytics");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse p-6">
        <div className="h-8 w-48 rounded bg-[var(--bg-tertiary)]" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-[var(--bg-tertiary)]" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 rounded-xl bg-[var(--bg-tertiary)]" />
          <div className="h-80 rounded-xl bg-[var(--bg-tertiary)]" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center justify-center py-20"
        style={{ color: "var(--color-error, #EF4444)" }}
      >
        {error}
      </div>
    );
  }

  const funnel = analytics?.conversion_funnel ?? [];
  const velocity = analytics?.velocity ?? [];
  const stageDuration = analytics?.stage_duration ?? [];
  const valueOverTime = analytics?.value_over_time ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/pipeline"
          className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Pipeline Analytics</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Conversion rates, velocity, and pipeline health
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Win Rate"
          value={`${analytics?.win_rate ?? 0}%`}
          icon={<Target className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Deal Size"
          value={formatCurrency(analytics?.avg_deal_size ?? 0)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Cycle Time"
          value={`${analytics?.avg_cycle_days ?? 0}d`}
          icon={<Clock className="h-4 w-4" />}
        />
        <MetricCard
          label="Total Pipeline"
          value={formatCurrency(analytics?.total_pipeline ?? 0)}
          icon={<BarChart3 className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <FunnelChart data={funnel} />
          {(analytics?.conversion_rate_lead_to_close ?? 0) > 0 && (
            <div className="mt-3 text-center">
              <span className="text-xs text-[var(--text-muted)]">
                Lead → Close Conversion:{" "}
                <span className="font-semibold text-[var(--muhide-orange)]">
                  {analytics?.conversion_rate_lead_to_close}%
                </span>
              </span>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <VelocityChart data={velocity} />
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
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
              title="Pipeline Value Over Time"
              height={220}
            />
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <StageDurationTable data={stageDuration} />
        </div>
      </div>
    </div>
  );
}
