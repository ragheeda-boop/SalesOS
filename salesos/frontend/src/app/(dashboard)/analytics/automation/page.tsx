"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { useWorkflows, type Workflow } from "@/lib/workflowQueries";
import { cn } from "@salesos/ui";
import { Badge } from "@salesos/ui";
import { BarChart, PieChart, MetricCard } from "@salesos/charts";
import { ExportShareBar } from "@/components/analytics";
import {
  ArrowLeft,
  Workflow as WorkflowIcon,
  CheckCircle,
  Clock,
  Play,
  RefreshCw,
} from "lucide-react";

interface AutomationMetrics {
  total_workflows: number;
  active_workflows: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  completion_rate: number;
  avg_duration_seconds: number;
  failure_rate: number;
  executions_over_time: {
    date: string;
    count: number;
    success: number;
    failed: number;
  }[];
  top_workflows: {
    id: string;
    name: string;
    runs: number;
    success_rate: number;
  }[];
}

const DATE_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
] as const;

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
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

export default function AutomationAnalyticsOverviewPage() {
  const { data: workflows, isLoading: workflowsLoading } = useWorkflows();
  const [analytics, setAnalytics] = useState<AutomationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/api/v1/workflows/analytics", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      setAnalytics(res.data);
    } catch {
      if (workflows) {
        const active = workflows.filter((w: Workflow) => w.status === "active").length;
        setAnalytics({
          total_workflows: workflows.length,
          active_workflows: active,
          total_executions: 0,
          successful_executions: 0,
          failed_executions: 0,
          completion_rate: 0,
          avg_duration_seconds: 0,
          failure_rate: 0,
          executions_over_time: [],
          top_workflows: workflows.map((w: Workflow) => ({
            id: w.id,
            name: w.name,
            runs: 0,
            success_rate: 0,
          })),
        });
      } else {
        setError("Failed to load automation analytics");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange, workflows]);

  if (loading || workflowsLoading) return <LoadingSkeleton />;

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

  const executionsData = analytics.executions_over_time.map((d) => ({
    label: d.date,
    value: d.success,
    color: "#10B981",
  }));

  const failedData = analytics.executions_over_time.map((d) => ({
    label: d.date,
    value: d.failed,
    color: "#EF4444",
  }));

  const wonLostData = [
    {
      label: "Successful",
      value: analytics.successful_executions,
      color: "#10B981",
    },
    { label: "Failed", value: analytics.failed_executions, color: "#EF4444" },
  ];

  const topWorkflowData = analytics.top_workflows.slice(0, 5).map((w) => ({
    label: w.name,
    value: w.runs,
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
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Automation Analytics</h1>
            <p className="text-sm text-[var(--text-muted)]">
              Workflow execution, completion rates, and performance
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
          <ExportShareBar reportName="Automation Analytics" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Active Workflows"
          value={String(analytics.active_workflows)}
          icon={<WorkflowIcon className="h-4 w-4" />}
        />
        <MetricCard
          label="Total Executions"
          value={String(analytics.total_executions)}
          icon={<Play className="h-4 w-4" />}
        />
        <MetricCard
          label="Completion Rate"
          value={`${analytics.completion_rate}%`}
          icon={<CheckCircle className="h-4 w-4" />}
        />
        <MetricCard
          label="Avg Duration"
          value={formatDuration(analytics.avg_duration_seconds)}
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Successful Executions</p>
          <p className="text-2xl font-bold text-[var(--status-success-text)]">
            {analytics.successful_executions}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Failed Executions</p>
          <p className="text-2xl font-bold text-[var(--status-danger-text)]">
            {analytics.failed_executions}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <p className="text-xs text-[var(--text-muted)]">Failure Rate</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{analytics.failure_rate}%</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Successful Executions Over Time
          </h3>
          <BarChart data={executionsData} height={250} />
        </div>

        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Failed Executions Over Time
          </h3>
          <BarChart data={failedData} height={250} />
        </div>
      </div>

      {/* Win/Loss + Top Workflows */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Success/Failure Ratio
          </h3>
          <PieChart data={wonLostData} height={200} />
        </div>

        <div className="lg:col-span-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Top Workflows</h3>
          <BarChart data={topWorkflowData} height={200} />
        </div>
      </div>

      {/* Top Workflows Table */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
          Workflow Performance
        </h3>
        <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Workflow
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Runs
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Success Rate
                </th>
                <th className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)]">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody>
              {analytics.top_workflows.map((wf) => (
                <tr
                  key={wf.id}
                  className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-3 py-2 font-medium text-[var(--text-primary)]">{wf.name}</td>
                  <td className="px-3 py-2 text-[var(--text-secondary)]">{wf.runs}</td>
                  <td className="px-3 py-2">
                    <Badge
                      variant={
                        wf.success_rate >= 80
                          ? "success"
                          : wf.success_rate >= 50
                            ? "warning"
                            : "danger"
                      }
                    >
                      {wf.success_rate}%
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-20 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${wf.success_rate}%`,
                            backgroundColor:
                              wf.success_rate >= 80
                                ? "#10B981"
                                : wf.success_rate >= 50
                                  ? "#F59E0B"
                                  : "#EF4444",
                          }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
              {analytics.top_workflows.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-3 py-6 text-center text-xs text-[var(--text-muted)]"
                  >
                    No workflow data available
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
