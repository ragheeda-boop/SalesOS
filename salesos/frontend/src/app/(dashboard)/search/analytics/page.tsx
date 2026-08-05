"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { BarChart, LineChart, MetricCard } from "@salesos/charts";
import { useTranslation } from "@/lib/i18n";
import { ArrowLeft, Search, Clock, TrendingUp, AlertTriangle } from "lucide-react";

interface TopQuery {
  query: string;
  count: number;
  avg_results: number;
}

interface LatencyBucket {
  label: string;
  p50: number;
  p95: number;
  p99: number;
}

interface VolumePoint {
  date: string;
  count: number;
}

interface SearchAnalyticsResponse {
  total_queries: number;
  zero_result_rate: number;
  avg_latency_ms: number;
  top_queries: TopQuery[];
  latency_distribution: LatencyBucket[];
  volume_over_time: VolumePoint[];
  period: { from: string; to: string };
}

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

function ZeroResultGauge({ rate }: { rate: number }) {
  const color =
    rate < 5
      ? "text-[var(--status-success-text)]"
      : rate < 15
        ? "text-[var(--status-warning-text)]"
        : "text-[var(--status-danger-text)]";
  const bg =
    rate < 5
      ? "bg-[var(--status-success-bg)] dark:bg-green-950/30"
      : rate < 15
        ? "bg-[var(--status-warning-bg)] dark:bg-amber-950/30"
        : "bg-[var(--status-danger-bg)] dark:bg-red-950/30";
  return (
    <div className={cn("rounded-xl border border-[var(--border-default)] p-4", bg)}>
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="h-4 w-4 text-[var(--text-muted)]" />
        <span className="text-sm font-medium text-[var(--text-muted)]">Zero-Result Rate</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={cn("text-3xl font-bold", color)}>{rate.toFixed(1)}%</span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            color.replace("text-", "bg-")
          )}
          style={{ width: `${Math.min(rate, 100)}%` }}
        />
      </div>
      <p className="mt-1.5 text-xs text-[var(--text-muted)]">
        {rate < 5 ? "Healthy" : rate < 15 ? "Acceptable" : "Needs attention"}
      </p>
    </div>
  );
}

function LatencyChart({ data }: { data: LatencyBucket[] }) {
  const chartData = data.map((d) => ({
    label: d.label,
    value: d.p95,
    color: d.p95 < 50 ? "#22C55E" : d.p95 < 200 ? "#F59E0B" : "#EF4444",
  }));
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">
        Latency Distribution (p95)
      </h3>
      <BarChart data={chartData} height={200} />
      <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-green-500" /> &lt;50ms
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-amber-500" /> 50-200ms
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-red-500" /> &gt;200ms
        </span>
      </div>
    </div>
  );
}

function LatencyTable({ data }: { data: LatencyBucket[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">Latency Percentiles</h3>
      <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
              <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                Strategy
              </th>
              <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                p50
              </th>
              <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                p95
              </th>
              <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                p99
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr
                key={item.label}
                className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
              >
                <td className="px-3 py-2 text-[var(--text-primary)]">{item.label}</td>
                <td className="px-3 py-2 text-[var(--text-secondary)]">{item.p50.toFixed(1)}ms</td>
                <td className="px-3 py-2 text-[var(--text-secondary)]">{item.p95.toFixed(1)}ms</td>
                <td className="px-3 py-2 text-[var(--text-secondary)]">{item.p99.toFixed(1)}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function SearchAnalyticsPage() {
  const { t } = useTranslation();
  const [analytics, setAnalytics] = useState<SearchAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rangeDays, setRangeDays] = useState<30 | 7 | 90>(30);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get("/api/v1/search/analytics", {
          params: { days: rangeDays },
          signal: controller.signal,
        });
        setAnalytics(res.data);
      } catch (err: unknown) {
        if ((err as Error)?.name !== "AbortError") {
          setError("Failed to load search analytics");
        }
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => controller.abort();
  }, [rangeDays]);

  const topQueriesChart = useMemo(() => {
    if (!analytics?.top_queries) return [];
    return analytics.top_queries.slice(0, 10).map((q) => ({
      label: q.query.length > 20 ? q.query.slice(0, 18) + "…" : q.query,
      value: q.count,
    }));
  }, [analytics?.top_queries]);

  const volumeChart = useMemo(() => {
    if (!analytics?.volume_over_time) return [];
    return analytics.volume_over_time.map((v) => ({
      label: v.date.slice(5),
      value: v.count,
    }));
  }, [analytics?.volume_over_time]);

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
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-sm" style={{ color: "var(--color-error, #EF4444)" }}>
          {error}
        </p>
        <Link
          href="/search"
          className="text-sm font-medium text-[var(--muhide-orange)] hover:underline"
        >
          Back to Search
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/search"
            className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {t("analytics.search_analytics")}
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              Query performance, popular searches, and latency metrics
            </p>
          </div>
        </div>

        {/* Date range filter */}
        <div className="flex gap-1 rounded-lg bg-[var(--bg-secondary)] p-1">
          {DATE_RANGES.map((r) => (
            <button
              key={r.days}
              onClick={() => setRangeDays(r.days as typeof rangeDays)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                rangeDays === r.days
                  ? "bg-[var(--bg-primary)] text-[var(--muhide-orange)] shadow-sm dark:text-orange-300"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label={t("analytics.total_queries")}
          value={String(analytics?.total_queries ?? 0)}
          icon={<Search className="h-4 w-4" />}
        />
        <MetricCard
          label="Zero-Result Rate"
          value={`${(analytics?.zero_result_rate ?? 0).toFixed(1)}%`}
          icon={<AlertTriangle className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Latency"
          value={`${(analytics?.avg_latency_ms ?? 0).toFixed(0)}ms`}
          icon={<Clock className="h-4 w-4" />}
        />
        <MetricCard
          label="Unique Queries"
          value={String(analytics?.top_queries?.length ?? 0)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Queries Bar Chart */}
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            {t("analytics.top_queries")}
          </h3>
          {topQueriesChart.length > 0 ? (
            <BarChart data={topQueriesChart} height={280} />
          ) : (
            <div className="flex h-[280px] items-center justify-center text-sm text-[var(--text-muted)]">
              No query data available
            </div>
          )}
        </div>

        {/* Zero-Result Rate Gauge */}
        <div className="space-y-6">
          <ZeroResultGauge rate={analytics?.zero_result_rate ?? 0} />
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <LatencyTable data={analytics?.latency_distribution ?? []} />
          </div>
        </div>

        {/* Search Volume Over Time */}
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            Search Volume Over Time
          </h3>
          {volumeChart.length > 0 ? (
            <LineChart
              series={[
                {
                  name: "Queries",
                  color: "#F57C1E",
                  data: volumeChart.map((v) => v.value),
                },
              ]}
              height={220}
            />
          ) : (
            <div className="flex h-[220px] items-center justify-center text-sm text-[var(--text-muted)]">
              No volume data available
            </div>
          )}
        </div>

        {/* Latency Distribution Chart */}
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <LatencyChart data={analytics?.latency_distribution ?? []} />
        </div>
      </div>

      {/* Top Queries Table */}
      {analytics?.top_queries && analytics.top_queries.length > 0 && (
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            Top Queries Detail
          </h3>
          <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                  <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    #
                  </th>
                  <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    Query
                  </th>
                  <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    Count
                  </th>
                  <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    Avg Results
                  </th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_queries.map((q, i) => (
                  <tr
                    key={q.query}
                    className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                  >
                    <td className="px-3 py-2 text-[var(--text-muted)]">{i + 1}</td>
                    <td className="px-3 py-2 text-[var(--text-primary)] font-medium">{q.query}</td>
                    <td className="px-3 py-2 text-[var(--text-secondary)]">{q.count}</td>
                    <td className="px-3 py-2 text-[var(--text-secondary)]">
                      {q.avg_results.toFixed(0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
