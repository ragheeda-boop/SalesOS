"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { BarChart, LineChart, MetricCard } from "@salesos/charts";
import { useTranslation } from "@/lib/i18n";
import { ArrowLeft, Bot, Clock, TrendingUp, CheckCircle, BarChart3 } from "lucide-react";
import { getTenantId } from "@/lib/hooks/useTenant";

interface ToolTelemetry {
  tool_name: string;
  total_calls: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  avg_result_count: number;
}

interface LatencyBucket {
  label: string;
  p50: number;
  p95: number;
  p99: number;
}

interface ResultBucket {
  label: string;
  count: number;
}

interface VolumePoint {
  date: string;
  calls: number;
  successes: number;
  failures: number;
}

interface TelemetryResponse {
  summary: {
    total_calls: number;
    success_rate: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
  };
  tools: ToolTelemetry[];
  latency_distribution: LatencyBucket[];
  result_histogram: ResultBucket[];
  volume_over_time: VolumePoint[];
}

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

export default function CopilotTelemetryPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<TelemetryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rangeDays, setRangeDays] = useState<30 | 7 | 90>(30);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get("/api/v1/copilot/telemetry", {
          params: { days: rangeDays },
          headers: { "X-Tenant-Id": getTenantId() },
          signal: controller.signal,
        });
        setData(res.data);
      } catch (err: unknown) {
        if ((err as Error)?.name !== "AbortError") {
          setError("Failed to load telemetry data");
        }
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => controller.abort();
  }, [rangeDays]);

  const latencyChartData = useMemo(() => {
    if (!data?.latency_distribution) return [];
    return data.latency_distribution.map((d) => ({
      label: d.label,
      value: d.p95,
      color: d.p95 < 200 ? "#22C55E" : d.p95 < 1000 ? "#F59E0B" : "#EF4444",
    }));
  }, [data?.latency_distribution]);

  const resultHistogramData = useMemo(() => {
    if (!data?.result_histogram) return [];
    return data.result_histogram.map((d) => ({
      label: d.label,
      value: d.count,
    }));
  }, [data?.result_histogram]);

  const volumeChartData = useMemo(() => {
    if (!data?.volume_over_time) return [];
    return data.volume_over_time.map((v) => ({
      label: v.date.slice(5),
      value: v.calls,
    }));
  }, [data?.volume_over_time]);

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
          href="/copilot"
          className="text-sm font-medium text-[var(--muhide-orange)] hover:underline"
        >
          Back to Copilot
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/copilot"
            className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {t("copilot.telemetry_title")}
            </h1>
            <p className="text-sm text-[var(--text-muted)]">{t("copilot.telemetry_subtitle")}</p>
          </div>
        </div>
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label={t("copilot.telemetry_total_calls")}
          value={String(data?.summary?.total_calls ?? 0)}
          icon={<Bot className="h-4 w-4" />}
        />
        <MetricCard
          label={t("copilot.telemetry_success_rate")}
          value={`${(data?.summary?.success_rate ?? 0).toFixed(1)}%`}
          icon={<CheckCircle className="h-4 w-4" />}
          trend={
            data?.summary?.success_rate
              ? { direction: "up", percentage: data.summary.success_rate }
              : undefined
          }
        />
        <MetricCard
          label={t("copilot.telemetry_avg_latency")}
          value={`${(data?.summary?.avg_latency_ms ?? 0).toFixed(0)}ms`}
          icon={<Clock className="h-4 w-4" />}
        />
        <MetricCard
          label={t("copilot.telemetry_p95_latency")}
          value={`${(data?.summary?.p95_latency_ms ?? 0).toFixed(0)}ms`}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            {t("copilot.telemetry_latency_distribution")}
          </h3>
          {latencyChartData.length > 0 ? (
            <BarChart data={latencyChartData} height={220} />
          ) : (
            <div className="flex h-[220px] items-center justify-center text-sm text-[var(--text-muted)]">
              No latency data available
            </div>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-[var(--text-muted)]">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-green-500" /> &lt;200ms
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500" /> 200-1000ms
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-red-500" /> &gt;1000ms
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            {t("copilot.telemetry_result_histogram")}
          </h3>
          {resultHistogramData.length > 0 ? (
            <BarChart data={resultHistogramData} height={220} />
          ) : (
            <div className="flex h-[220px] items-center justify-center text-sm text-[var(--text-muted)]">
              No result data available
            </div>
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
            {t("copilot.telemetry_volume_over_time")}
          </h3>
          {volumeChartData.length > 0 ? (
            <LineChart
              series={[
                {
                  name: "Calls",
                  color: "#F57C1E",
                  data: volumeChartData.map((v) => v.value),
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

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <LatencyPercentileTable data={data?.latency_distribution ?? []} />
        </div>
      </div>

      {data?.tools && data.tools.length > 0 && (
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            {t("copilot.telemetry_tool_breakdown")}
          </h3>
          <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                  <th className="text-start px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_tool_name")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_calls")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_success")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_failure")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    Rate
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_p50")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_p95")}
                  </th>
                  <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {t("copilot.telemetry_p99")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.tools.map((tool) => (
                  <tr
                    key={tool.tool_name}
                    className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                  >
                    <td className="px-3 py-2 text-[var(--text-primary)] font-medium">
                      {tool.tool_name}
                    </td>
                    <td className="px-3 py-2 text-[var(--text-secondary)] text-end">
                      {tool.total_calls}
                    </td>
                    <td className="px-3 py-2 text-[var(--status-success-text)] text-end">
                      {tool.success_count}
                    </td>
                    <td className="px-3 py-2 text-[var(--status-danger-text)] text-end">
                      {tool.failure_count}
                    </td>
                    <td className="px-3 py-2 text-end">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[10px] font-medium",
                          tool.success_rate >= 95
                            ? "bg-[var(--status-success-bg)] text-[var(--status-success-text)]"
                            : tool.success_rate >= 80
                              ? "bg-[var(--status-warning-bg)] text-amber-700"
                              : "bg-[var(--status-danger-bg)] text-red-700"
                        )}
                      >
                        {tool.success_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                      {tool.latency_p50_ms.toFixed(0)}ms
                    </td>
                    <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                      {tool.latency_p95_ms.toFixed(0)}ms
                    </td>
                    <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                      {tool.latency_p99_ms.toFixed(0)}ms
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

function LatencyPercentileTable({ data }: { data: LatencyBucket[] }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">
        {t("copilot.telemetry_latency_distribution")}
      </h3>
      <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
              <th className="text-start px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                Tool
              </th>
              <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                {t("copilot.telemetry_p50")}
              </th>
              <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                {t("copilot.telemetry_p95")}
              </th>
              <th className="text-end px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                {t("copilot.telemetry_p99")}
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
                <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                  {item.p50.toFixed(1)}ms
                </td>
                <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                  {item.p95.toFixed(1)}ms
                </td>
                <td className="px-3 py-2 text-[var(--text-secondary)] text-end font-mono">
                  {item.p99.toFixed(1)}ms
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
