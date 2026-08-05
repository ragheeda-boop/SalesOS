"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { Badge } from "@salesos/ui";
import { BarChart, LineChart, PieChart, MetricCard } from "@salesos/charts";
import { ExportShareBar } from "@/components/analytics";
import {
  ArrowLeft,
  DollarSign,
  Target,
  Users,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import { normalizePipelineAnalytics } from "@/lib/pipelineAnalytics";

interface SalesMetrics {
  total_revenue: number;
  revenue_trend: number;
  deals_closed: number;
  deals_trend: number;
  avg_deal_size: number;
  avg_deal_trend: number;
  win_rate: number;
  win_rate_trend: number;
}

interface RevenueTrend {
  date: string;
  value: number;
}

interface DealStage {
  stage: string;
  count: number;
  value: number;
}

interface SalesRep {
  name: string;
  revenue: number;
  deals: number;
  win_rate: number;
}

interface SalesDashboardData {
  metrics: SalesMetrics;
  revenue_trend: RevenueTrend[];
  pipeline_by_stage: DealStage[];
  top_reps: SalesRep[];
  won_lost: { won: number; lost: number };
}

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`;
  return `${value.toLocaleString()} SAR`;
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

export default function SalesAnalyticsPage() {
  const [data, setData] = useState<SalesDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardRes, pipelineRes] = await Promise.all([
        api.get("/api/v1/revenue/dashboard"),
        api.get("/api/v1/pipeline/analytics"),
      ]);

      const dash = dashboardRes.data;
      const pipeline = normalizePipelineAnalytics(pipelineRes.data);

      const metrics: SalesMetrics = {
        total_revenue: dash?.total_value ?? 0,
        revenue_trend: 0,
        deals_closed: dash?.closed_won ?? 0,
        deals_trend: 0,
        avg_deal_size: dash?.avg_deal_size ?? 0,
        avg_deal_trend: 0,
        win_rate: pipeline.win_rate,
        win_rate_trend: 0,
      };

      const revenueTrend: RevenueTrend[] = [];

      const pipelineByStage: DealStage[] = pipeline.conversion_funnel.map(
        (s) => ({
          stage: s.stage,
          count: s.count,
          value: s.value,
        }),
      );

      const topReps: SalesRep[] = (dash?.active_opportunities ?? [])
        .slice(0, 5)
        .map((o: { name: string; value: number }) => ({
          name: o.name,
          revenue: o.value,
          deals: 0,
          win_rate: 0,
        }));

      setData({
        metrics,
        revenue_trend: revenueTrend,
        pipeline_by_stage: pipelineByStage,
        top_reps: topReps,
        won_lost: {
          won: metrics.deals_closed,
          lost: dash?.closed_lost ?? 0,
        },
      });
    } catch {
      setError("Failed to load sales analytics");
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

  if (!data) return null;

  const pipelineData = data.pipeline_by_stage.map((s) => ({
    label: s.stage.replace("_", ""),
    value: s.value,
  }));

  const wonLostData = [
    { label: "Won", value: data.won_lost.won, color: "#10B981" },
    { label: "Lost", value: data.won_lost.lost, color: "#EF4444" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/analytics"
            className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              Sales Analytics
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              Revenue, deals, and rep performance
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
                    : "bg-[var(--bg-primary)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]",
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
          <ExportShareBar reportName="Sales Analytics" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Revenue"
          value={formatCurrency(data.metrics.total_revenue)}
          trend={{
            direction: data.metrics.revenue_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.revenue_trend),
          }}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          label="Deals Closed"
          value={String(data.metrics.deals_closed)}
          trend={{
            direction: data.metrics.deals_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.deals_trend),
          }}
          icon={<Target className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Deal Size"
          value={formatCurrency(data.metrics.avg_deal_size)}
          trend={{
            direction: data.metrics.avg_deal_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.avg_deal_trend),
          }}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <MetricCard
          label="Win Rate"
          value={`${data.metrics.win_rate}%`}
          trend={{
            direction: data.metrics.win_rate_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.win_rate_trend),
          }}
          icon={<Users className="h-4 w-4" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Revenue Trend
          </h3>
          <LineChart
            series={[
              {
                name: "Revenue",
                color: "#F57C1E",
                data: data.revenue_trend.map((d) => d.value),
              },
            ]}
            height={250}
          />
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Pipeline by Stage
          </h3>
          <BarChart data={pipelineData} height={250} />
        </div>
      </div>

      {/* Won/Lost + Top Reps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Win/Loss Ratio
          </h3>
          <PieChart data={wonLostData} height={200} />
        </div>

        <div className="lg:col-span-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Top Sales Reps
          </h3>
          <div className="space-y-3">
            {data.top_reps.map((rep, i) => (
              <div
                key={rep.name}
                className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-[var(--bg-secondary)] transition"
              >
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
                    i === 0
                      ? "bg-yellow-100 text-yellow-700"
                      : i === 1
                        ? "bg-gray-100 text-gray-600"
                        : "bg-[var(--bg-tertiary)] text-[var(--text-muted)]",
                  )}
                >
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                    {rep.name}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {rep.deals} deals closed
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {formatCurrency(rep.revenue)}
                  </p>
                  <Badge
                    variant={
                      rep.win_rate >= 65
                        ? "success"
                        : rep.win_rate >= 50
                          ? "warning"
                          : "danger"
                    }
                  >
                    {rep.win_rate}% win rate
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
