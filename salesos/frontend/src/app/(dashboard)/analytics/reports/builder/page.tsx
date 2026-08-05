"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { cn } from "@salesos/ui";
import {
  Badge,
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
} from "@salesos/ui";
import { BarChart } from "@salesos/charts";
import { ArrowLeft, Save, Eye, BarChart3, Table } from "lucide-react";

interface MetricOption {
  id: string;
  label: string;
  domain: string;
  format: "currency" | "number" | "percentage";
}

interface DimensionOption {
  id: string;
  label: string;
}

interface ReportConfig {
  name: string;
  metrics: string[];
  dimensions: string[];
  filters: {
    date_from: string;
    date_to: string;
    domain: string;
    status: string;
  };
  viz_type: "chart" | "table" | "both";
  group_by: string;
  aggregation: string;
}

interface ReportPreview {
  metrics: { label: string; value: string; trend?: number }[];
  chart_data: { label: string; value: number }[];
  table_data: Record<string, string | number>[];
}

const METRICS: MetricOption[] = [
  {
    id: "revenue",
    label: "Total Revenue",
    domain: "Revenue",
    format: "currency",
  },
  { id: "arr", label: "ARR", domain: "Revenue", format: "currency" },
  {
    id: "nrr",
    label: "Net Revenue Retention",
    domain: "Revenue",
    format: "percentage",
  },
  {
    id: "churn_rate",
    label: "Churn Rate",
    domain: "Revenue",
    format: "percentage",
  },
  {
    id: "pipeline_value",
    label: "Pipeline Value",
    domain: "Pipeline",
    format: "currency",
  },
  {
    id: "win_rate",
    label: "Win Rate",
    domain: "Pipeline",
    format: "percentage",
  },
  {
    id: "avg_deal_size",
    label: "Avg Deal Size",
    domain: "Pipeline",
    format: "currency",
  },
  {
    id: "deals_closed",
    label: "Deals Closed",
    domain: "Sales",
    format: "number",
  },
  {
    id: "conversion_rate",
    label: "Conversion Rate",
    domain: "Sales",
    format: "percentage",
  },
  {
    id: "employee_count",
    label: "Employee Count",
    domain: "Employees",
    format: "number",
  },
  {
    id: "avg_score",
    label: "Avg Performance Score",
    domain: "Employees",
    format: "number",
  },
  {
    id: "workflow_runs",
    label: "Workflow Executions",
    domain: "Automation",
    format: "number",
  },
  {
    id: "completion_rate",
    label: "Completion Rate",
    domain: "Automation",
    format: "percentage",
  },
];

const DIMENSIONS: DimensionOption[] = [
  { id: "time", label: "Time (Monthly)" },
  { id: "rep", label: "Sales Rep" },
  { id: "region", label: "Region" },
  { id: "product", label: "Product" },
  { id: "department", label: "Department" },
  { id: "domain", label: "Domain" },
];

const DOMAINS = ["All", "Revenue", "Pipeline", "Sales", "Employees", "Automation"];
const STATUSES = ["All", "Active", "Closed", "Pending"];

function formatValue(value: number, format: "currency" | "number" | "percentage"): string {
  if (format === "currency") {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M SAR`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K SAR`;
    return `${value.toLocaleString()} SAR`;
  }
  if (format === "percentage") return `${value}%`;
  return value.toLocaleString();
}

function generatePreview(config: ReportConfig): ReportPreview {
  // Honest empty preview — do not invent Math.random metrics.
  const selectedMetrics = METRICS.filter((m) => config.metrics.includes(m.id));
  const metrics = selectedMetrics.map((m) => ({
    label: m.label,
    value: formatValue(0, m.format),
    trend: 0,
  }));
  return { metrics, chart_data: [], table_data: [] };
}

export default function ReportBuilderPage() {
  const [config, setConfig] = useState<ReportConfig>({
    name: "",
    metrics: ["revenue", "pipeline_value", "win_rate"],
    dimensions: ["time"],
    filters: { date_from: "", date_to: "", domain: "All", status: "All" },
    viz_type: "both",
    group_by: "time",
    aggregation: "sum",
  });

  const [showSaveModal, setShowSaveModal] = useState(false);
  const [reportName, setReportName] = useState("");
  const [saved, setSaved] = useState(false);

  const preview = useMemo(() => generatePreview(config), [config]);

  const toggleMetric = useCallback((id: string) => {
    setConfig((prev) => ({
      ...prev,
      metrics: prev.metrics.includes(id)
        ? prev.metrics.filter((m) => m !== id)
        : [...prev.metrics, id],
    }));
  }, []);

  const toggleDimension = useCallback((id: string) => {
    setConfig((prev) => ({
      ...prev,
      dimensions: prev.dimensions.includes(id)
        ? prev.dimensions.filter((d) => d !== id)
        : [...prev.dimensions, id],
    }));
  }, []);

  const handleSave = () => {
    if (reportName.trim()) {
      setConfig((prev) => ({ ...prev, name: reportName.trim() }));
      setSaved(true);
      setShowSaveModal(false);
      setTimeout(() => setSaved(false), 3000);
    }
  };

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
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Report Builder</h1>
            <p className="text-sm text-[var(--text-muted)]">
              Configure metrics, dimensions, and filters
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {saved && <Badge variant="success">Report saved!</Badge>}
          <Modal open={showSaveModal} onOpenChange={setShowSaveModal}>
            <ModalTrigger asChild>
              <button className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition">
                <Save className="h-4 w-4" /> Save Report
              </button>
            </ModalTrigger>
            <ModalContent>
              <ModalHeader>
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">Save Report</h2>
              </ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-[var(--text-muted)]">Report Name</label>
                    <Input
                      value={reportName}
                      onChange={(e) => setReportName(e.target.value)}
                      placeholder="e.g., Monthly Revenue Summary"
                      className="mt-1"
                    />
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    {config.metrics.length} metrics, {config.dimensions.length} dimensions,{" "}
                    {config.viz_type} view
                  </div>
                </div>
              </ModalBody>
              <ModalFooter>
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="rounded-lg border border-[var(--border-default)] px-4 py-2 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!reportName.trim()}
                  className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm text-white hover:opacity-90 transition disabled:opacity-50"
                >
                  Save
                </button>
              </ModalFooter>
            </ModalContent>
          </Modal>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-4">
          {/* Metric Picker */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Metrics</h3>
            <div className="space-y-2">
              {METRICS.map((metric) => (
                <label
                  key={metric.id}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition",
                    config.metrics.includes(metric.id)
                      ? "bg-[var(--muhide-orange)]/10 border border-[var(--muhide-orange)]/30"
                      : "hover:bg-[var(--bg-secondary)] border border-transparent"
                  )}
                >
                  <input
                    type="checkbox"
                    checked={config.metrics.includes(metric.id)}
                    onChange={() => toggleMetric(metric.id)}
                    className="rounded border-[var(--border-default)]"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-[var(--text-primary)]">{metric.label}</p>
                    <p className="text-[10px] text-[var(--text-muted)]">{metric.domain}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Dimension Picker */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Group By</h3>
            <div className="space-y-2">
              {DIMENSIONS.map((dim) => (
                <label
                  key={dim.id}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition",
                    config.dimensions.includes(dim.id)
                      ? "bg-[var(--muhide-orange)]/10 border border-[var(--muhide-orange)]/30"
                      : "hover:bg-[var(--bg-secondary)] border border-transparent"
                  )}
                >
                  <input
                    type="checkbox"
                    checked={config.dimensions.includes(dim.id)}
                    onChange={() => toggleDimension(dim.id)}
                    className="rounded border-[var(--border-default)]"
                  />
                  <span className="text-xs font-medium text-[var(--text-primary)]">
                    {dim.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Filter Builder */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Filters</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-[var(--text-muted)]">Date Range</label>
                <div className="flex gap-2 mt-1">
                  <Input
                    type="date"
                    value={config.filters.date_from}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        filters: { ...prev.filters, date_from: e.target.value },
                      }))
                    }
                    className="flex-1 text-xs"
                  />
                  <Input
                    type="date"
                    value={config.filters.date_to}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        filters: { ...prev.filters, date_to: e.target.value },
                      }))
                    }
                    className="flex-1 text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-[var(--text-muted)]">Domain</label>
                <select
                  value={config.filters.domain}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      filters: { ...prev.filters, domain: e.target.value },
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-xs text-[var(--text-primary)]"
                >
                  {DOMAINS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-[var(--text-muted)]">Status</label>
                <select
                  value={config.filters.status}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      filters: { ...prev.filters, status: e.target.value },
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-xs text-[var(--text-primary)]"
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Visualization Type */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Visualization</h3>
            <div className="flex gap-2">
              {[
                {
                  id: "chart" as const,
                  label: "Chart",
                  icon: <BarChart3 className="h-4 w-4" />,
                },
                {
                  id: "table" as const,
                  label: "Table",
                  icon: <Table className="h-4 w-4" />,
                },
                {
                  id: "both" as const,
                  label: "Both",
                  icon: <Eye className="h-4 w-4" />,
                },
              ].map((v) => (
                <button
                  key={v.id}
                  onClick={() => setConfig((prev) => ({ ...prev, viz_type: v.id }))}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition",
                    config.viz_type === v.id
                      ? "bg-[var(--muhide-orange)] text-white"
                      : "border border-[var(--border-default)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
                  )}
                >
                  {v.icon}
                  {v.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
              Preview{config.name ? `: ${config.name}` : ""}
            </h3>

            {/* Metric Cards */}
            {config.metrics.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                {preview.metrics.map((m) => (
                  <div
                    key={m.label}
                    className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3"
                  >
                    <p className="text-[10px] text-[var(--text-muted)]">{m.label}</p>
                    <p className="text-lg font-bold text-[var(--text-primary)]">{m.value}</p>
                    {m.trend !== undefined && (
                      <p
                        className={cn(
                          "text-[10px]",
                          m.trend >= 0
                            ? "text-[var(--status-success-text)]"
                            : "text-[var(--status-danger-text)]"
                        )}
                      >
                        {m.trend >= 0 ? "+" : ""}
                        {m.trend}%
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Chart */}
            {(config.viz_type === "chart" || config.viz_type === "both") && (
              <div className="mb-6">
                <BarChart data={preview.chart_data} height={250} />
              </div>
            )}

            {/* Table */}
            {(config.viz_type === "table" || config.viz_type === "both") && (
              <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)]">
                      {Object.keys(preview.table_data[0] ?? {}).map((key) => (
                        <th
                          key={key}
                          className="text-right px-3 py-2 text-xs font-medium text-[var(--text-muted)] capitalize"
                        >
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.table_data.map((row, i) => (
                      <tr
                        key={i}
                        className="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--bg-secondary)]"
                      >
                        {Object.values(row).map((val, j) => (
                          <td key={j} className="px-3 py-2 text-[var(--text-secondary)]">
                            {typeof val === "number" ? val.toLocaleString() : val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {config.metrics.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <BarChart3 className="h-8 w-8 text-[var(--text-muted)] mb-2" />
                <p className="text-sm text-[var(--text-muted)]">
                  Select metrics to preview your report
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
