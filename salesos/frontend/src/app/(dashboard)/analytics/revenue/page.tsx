"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { BarChart, LineChart, MetricCard } from "@salesos/charts";
import { ExportShareBar } from "@/components/analytics";
import { ArrowLeft, DollarSign, TrendingUp, TrendingDown, Target, RefreshCw } from "lucide-react";

interface RevenueMetrics {
  arr: number;
  arr_trend: number;
  nrr: number;
  nrr_trend: number;
  churn_rate: number;
  churn_trend: number;
  expansion_revenue: number;
  expansion_trend: number;
  mrr: number;
  ltv: number;
}

interface TrendPoint {
  date: string;
  value: number;
}

interface ForecastVsActual {
  month: string;
  forecast: number;
  actual: number;
}

interface RevenueDashboardData {
  metrics: RevenueMetrics;
  arr_trend: TrendPoint[];
  nrr_trend: TrendPoint[];
  forecast_vs_actual: ForecastVsActual[];
  revenue_by_region: { region: string; value: number }[];
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

export default function RevenueAnalyticsPage() {
  const [data, setData] = useState<RevenueDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardRes, forecastRes, workspaceRes] = await Promise.all([
        api.get("/api/v1/revenue/dashboard"),
        api.get("/api/v1/forecast").catch(() => ({ data: null })),
        api.get("/api/v1/workspace").catch(() => ({ data: null })),
      ]);

      const dash = dashboardRes.data;
      const forecast = forecastRes.data;
      const workspace = workspaceRes.data;

      const arr =
        workspace?.kpis?.revenue?.value ??
        workspace?.opportunities?.total_value ??
        dash?.total_value ??
        0;
      const metrics: RevenueMetrics = {
        arr,
        arr_trend: workspace?.kpis?.revenue?.change ?? 0,
        nrr: workspace?.kpis?.nrr?.value ?? 0,
        nrr_trend: workspace?.kpis?.nrr?.change ?? 0,
        churn_rate: workspace?.kpis?.churn?.value ?? 0,
        churn_trend: workspace?.kpis?.churn?.change ?? 0,
        expansion_revenue: workspace?.kpis?.forecast?.value ?? 0,
        expansion_trend: workspace?.kpis?.forecast?.change ?? 0,
        mrr: arr ? Math.round(arr / 12) : 0,
        ltv: 0,
      };

      setData({
        metrics,
        arr_trend: [],
        nrr_trend: [],
        forecast_vs_actual: [],
        revenue_by_region: [],
      });
      void forecast;
    } catch {
      setError("Failed to load revenue analytics");
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

  const regionData = data.revenue_by_region.map((r) => ({
    label: r.region,
    value: r.value,
  }));

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
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Revenue Analytics</h1>
            <p className="text-sm text-[var(--text-muted)]">
              ARR, NRR, churn, and forecast tracking
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
          <ExportShareBar reportName="Revenue Analytics" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="ARR"
          value={formatCurrency(data.metrics.arr)}
          trend={{
            direction: data.metrics.arr_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.arr_trend),
          }}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          label="MRR"
          value={formatCurrency(data.metrics.mrr)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          label="NRR"
          value={`${data.metrics.nrr}%`}
          trend={{
            direction: data.metrics.nrr_trend >= 0 ? "up" : "down",
            percentage: Math.abs(data.metrics.nrr_trend),
          }}
          icon={<Target className="h-4 w-4" />}
        />
        <MetricCard
          label="Customer LTV"
          value={formatCurrency(data.metrics.ltv)}
          icon={<DollarSign className="h-4 w-4" />}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Churn Rate</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            {data.metrics.churn_rate}%
          </p>
          <div
            className={cn(
              "flex items-center gap-1 mt-1 text-xs",
              data.metrics.churn_trend >= 0
                ? "text-[var(--status-success-text)]"
                : "text-[var(--status-danger-text)]"
            )}
          >
            {data.metrics.churn_trend >= 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span>{Math.abs(data.metrics.churn_trend)}% vs last period</span>
          </div>
        </div>
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Expansion Revenue</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            {formatCurrency(data.metrics.expansion_revenue)}
          </p>
          <div
            className={cn(
              "flex items-center gap-1 mt-1 text-xs",
              data.metrics.expansion_trend >= 0
                ? "text-[var(--status-success-text)]"
                : "text-[var(--status-danger-text)]"
            )}
          >
            {data.metrics.expansion_trend >= 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span>{Math.abs(data.metrics.expansion_trend)}% vs last period</span>
          </div>
        </div>
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Net Revenue Retention</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{data.metrics.nrr}%</p>
          <div
            className={cn(
              "flex items-center gap-1 mt-1 text-xs",
              data.metrics.nrr_trend >= 0
                ? "text-[var(--status-success-text)]"
                : "text-[var(--status-danger-text)]"
            )}
          >
            {data.metrics.nrr_trend >= 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span>{Math.abs(data.metrics.nrr_trend)}% vs last period</span>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">ARR Trend</h3>
          <LineChart
            series={[
              {
                name: "ARR",
                color: "#3B82F6",
                data: data.arr_trend.map((d) => d.value),
              },
            ]}
            height={250}
          />
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">NRR Trend</h3>
          <LineChart
            series={[
              {
                name: "NRR",
                color: "#10B981",
                data: data.nrr_trend.map((d) => d.value),
              },
            ]}
            height={250}
          />
        </div>
      </div>

      {/* Forecast vs Actual + Revenue by Region */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Forecast vs Actual
          </h3>
          <div className="space-y-2">
            {data.forecast_vs_actual.map((d) => {
              const maxVal = Math.max(
                ...data.forecast_vs_actual.map((f) => Math.max(f.forecast, f.actual)),
                1
              );
              return (
                <div key={d.month} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                    <span>{d.month}</span>
                    <span>
                      Actual: {formatCurrency(d.actual)} / Forecast: {formatCurrency(d.forecast)}
                    </span>
                  </div>
                  <div className="relative h-5 rounded bg-[var(--bg-tertiary)] overflow-hidden">
                    <div
                      className="absolute inset-y-0 start-0 rounded bg-green-500/60 transition-all"
                      style={{ width: `${(d.actual / maxVal) * 100}%` }}
                    />
                    <div
                      className="absolute inset-y-0 start-0 rounded border-2 border-dashed border-[var(--muhide-orange)]"
                      style={{ width: `${(d.forecast / maxVal) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
            <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-sm bg-green-500/60" /> Actual
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-sm border border-dashed border-[var(--muhide-orange)]" />{" "}
                Forecast
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Revenue by Region
          </h3>
          <BarChart data={regionData} height={250} />
        </div>
      </div>
    </div>
  );
}
