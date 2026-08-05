"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { cn } from "@salesos/ui";
import { Badge } from "@salesos/ui";
import { BarChart, LineChart, PieChart, MetricCard } from "@salesos/charts";
import { ExportShareBar } from "@/components/analytics";
import { ArrowLeft, Users, Target, RefreshCw, Activity, Brain } from "lucide-react";

interface EmployeeMetrics {
  total_employees: number;
  active_employees: number;
  avg_score: number;
  score_trend: number;
  avg_signals: number;
  signals_trend: number;
  departments: { name: string; count: number; avg_score: number }[];
  score_distribution: { range: string; count: number }[];
  score_trend_over_time: { date: string; value: number }[];
  top_performers: { name: string; score: number; department: string }[];
}

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

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

export default function EmployeesAnalyticsPage() {
  const [data, setData] = useState<EmployeeMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/api/v1/employees", {
        params: { limit: 100 },
      });
      const employees = res.data?.employees ?? res.data ?? [];

      const totalEmployees = employees.length;
      const activeEmployees = employees.filter(
        (e: { status?: string }) => e.status !== "inactive"
      ).length;
      const scores = employees
        .map((e: { score?: number | null }) => e.score)
        .filter((s: number | null | undefined): s is number => s != null);
      const avgScore =
        scores.length > 0
          ? Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
          : 0;

      const departments: Record<string, { count: number; total_score: number }> = {};
      employees.forEach((e: { department?: string; score?: number | null }) => {
        const dept = e.department || "Unknown";
        if (!departments[dept]) departments[dept] = { count: 0, total_score: 0 };
        departments[dept].count++;
        if (e.score != null) departments[dept].total_score += e.score;
      });

      const deptData = Object.entries(departments).map(([name, d]) => ({
        name,
        count: d.count,
        avg_score: d.count > 0 ? Math.round(d.total_score / d.count) : 0,
      }));

      const scoreRanges = [
        {
          range: "90-100",
          count: scores.filter((s: number) => s >= 90).length,
        },
        {
          range: "70-89",
          count: scores.filter((s: number) => s >= 70 && s < 90).length,
        },
        {
          range: "50-69",
          count: scores.filter((s: number) => s >= 50 && s < 70).length,
        },
        { range: "0-49", count: scores.filter((s: number) => s < 50).length },
      ];

      // Honest empty trend — do not fabricate historical score series.
      const scoreTrendOverTime: { date: string; value: number }[] = [];

      const topPerformers = employees
        .filter((e: { score?: number | null }) => e.score != null)
        .sort((a: { score: number }, b: { score: number }) => b.score - a.score)
        .slice(0, 5)
        .map(
          (e: {
            name?: string;
            first_name?: string;
            last_name?: string;
            score: number;
            department?: string;
          }) => ({
            name: e.name || `${e.first_name ?? ""} ${e.last_name ?? ""}`.trim() || "Unknown",
            score: e.score,
            department: e.department || "Unknown",
          })
        );

      setData({
        total_employees: totalEmployees,
        active_employees: activeEmployees,
        avg_score: avgScore,
        score_trend: 0,
        avg_signals:
          employees.reduce(
            (sum: number, e: { signal_count?: number }) => sum + (e.signal_count ?? 0),
            0
          ) / Math.max(1, employees.length),
        signals_trend: 0,
        departments: deptData.length > 0 ? deptData : [],
        score_distribution: scoreRanges,
        score_trend_over_time: scoreTrendOverTime,
        top_performers: topPerformers.length > 0 ? topPerformers : [],
      });
    } catch {
      setError("Failed to load employee analytics");
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

  const deptChartData = data.departments.map((d) => ({
    label: d.name,
    value: d.avg_score,
  }));

  const distData = data.score_distribution.map((d) => ({
    label: d.range,
    value: d.count,
    color:
      d.range === "90-100"
        ? "#10B981"
        : d.range === "70-89"
          ? "#3B82F6"
          : d.range === "50-69"
            ? "#F59E0B"
            : "#EF4444",
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
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Employee Analytics</h1>
            <p className="text-sm text-[var(--text-muted)]">
              Performance scores, signals, and department breakdown
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
          <ExportShareBar reportName="Employee Analytics" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Employees"
          value={String(data.total_employees)}
          icon={<Users className="h-4 w-4" />}
        />
        <MetricCard
          label="Active Employees"
          value={String(data.active_employees)}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Score"
          value={String(data.avg_score)}
          icon={<Brain className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Signals"
          value={String(data.avg_signals)}
          icon={<Target className="h-4 w-4" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Score by Department
          </h3>
          <BarChart data={deptChartData} height={250} />
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Score Distribution
          </h3>
          <PieChart data={distData} height={200} />
        </div>
      </div>

      {/* Score Trend + Top Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Score Trend</h3>
          {data.score_trend_over_time.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)] py-10 text-center">
              No historical score series available. Trends are not invented.
            </p>
          ) : (
            <LineChart
              series={[
                {
                  name: "Avg Score",
                  color: "#8B5CF6",
                  data: data.score_trend_over_time.map((d) => d.value),
                },
              ]}
              height={250}
            />
          )}
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Top Performers</h3>
          <div className="space-y-3">
            {data.top_performers.map((emp, i) => (
              <div
                key={emp.name}
                className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-[var(--bg-secondary)] transition"
              >
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
                    i === 0
                      ? "bg-yellow-100 text-yellow-700"
                      : i === 1
                        ? "bg-gray-100 text-gray-600"
                        : "bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
                  )}
                >
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                    {emp.name}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">{emp.department}</p>
                </div>
                <div className="text-right">
                  <Badge
                    variant={emp.score >= 80 ? "success" : emp.score >= 60 ? "warning" : "danger"}
                  >
                    {emp.score}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Department Table */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
          Department Breakdown
        </h3>
        <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Department
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Headcount
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Avg Score
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody>
              {data.departments.map((dept) => (
                <tr
                  key={dept.name}
                  className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2 font-medium text-[var(--text-primary)]">{dept.name}</td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">{dept.count}</td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">{dept.avg_score}</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-20 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${dept.avg_score}%`,
                            backgroundColor:
                              dept.avg_score >= 75
                                ? "#10B981"
                                : dept.avg_score >= 50
                                  ? "#F59E0B"
                                  : "#EF4444",
                          }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
