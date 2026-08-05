"use client";

import { useTranslation } from "@/lib/i18n";
import { useCallback } from "react";
import { BarChart, PieChart, MetricCard, type ChartDataPoint } from "@salesos/charts";
import { Card, CardContent, CardHeader, Badge } from "@salesos/ui";
import {
  Download,
  TrendingUp,
  DollarSign,
  Target,
  BarChart3,
  Users,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { useExecutiveDashboard } from "@/lib/hooks/executiveQueries";

function formatCurrency(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value}`;
}

export function AnalyticsWorkspace() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useExecutiveDashboard();

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  if (isLoading) {
    return (
      <div role="region" aria-label={t("analytics.title")} className="space-y-6 p-6">
        <div className="space-y-2">
          <div className="h-7 w-48 rounded-lg bg-[var(--bg-secondary)] animate-pulse" />
          <div className="h-4 w-72 rounded bg-[var(--bg-secondary)] animate-pulse" />
        </div>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-[var(--bg-secondary)] animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-72 rounded-xl bg-[var(--bg-secondary)] animate-pulse" />
          <div className="h-72 rounded-xl bg-[var(--bg-secondary)] animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div role="region" aria-label={t("analytics.title")} className="p-6">
        <div
          className="rounded-xl border p-6"
          style={{
            borderColor: "var(--border-default)",
            background: "var(--bg-primary)",
          }}
        >
          <p className="text-sm" style={{ color: "var(--danger-600, #EF4444)" }}>
            {t("analytics.error")}
          </p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div role="region" aria-label={t("analytics.title")} className="p-6">
        <div
          className="rounded-xl border p-6 text-center"
          style={{
            borderColor: "var(--border-default)",
            background: "var(--bg-primary)",
          }}
        >
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {t("analytics.no_data")}
          </p>
        </div>
      </div>
    );
  }

  const { revenue, pipeline, growth, risk, team, renewals } = data;

  const pipelineStageData: ChartDataPoint[] = pipeline.by_stage.map((s) => ({
    label: s.stage,
    value: s.val,
  }));

  const conversionRate =
    pipeline.total_deals > 0 ? Math.round((pipeline.won_deals / pipeline.total_deals) * 100) : 0;

  const wonLostData: ChartDataPoint[] = [
    {
      label: t("analytics.won_deals"),
      value: pipeline.won_deals,
      color: "#22C55E",
    },
    {
      label: t("analytics.lost_deals"),
      value: pipeline.lost_deals,
      color: "#EF4444",
    },
  ];

  const growthData: ChartDataPoint[] = [
    {
      label: t("analytics.new_companies"),
      value: growth.new_companies_30d,
      color: "var(--chart-1)",
    },
    {
      label: t("analytics.new_contacts"),
      value: growth.new_contacts_30d,
      color: "#22C55E",
    },
    {
      label: t("analytics.new_opportunities"),
      value: growth.new_opportunities_30d,
      color: "#F59E0B",
    },
    {
      label: t("analytics.new_contracts"),
      value: growth.new_contracts_30d,
      color: "#A855F7",
    },
  ];

  const riskData: ChartDataPoint[] = [
    {
      label: t("analytics.stalled_deals"),
      value: risk.stalled_deals,
      color: "#EF4444",
    },
    {
      label: t("analytics.expiring_contracts"),
      value: risk.expiring_contracts,
      color: "#F59E0B",
    },
    {
      label: t("analytics.inactive_companies"),
      value: risk.inactive_companies,
      color: "#6B7280",
    },
  ];

  return (
    <div role="region" aria-label={t("analytics.title")} className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">{t("analytics.title")}</h1>
          <p className="text-sm text-[var(--text-muted)]">{t("analytics.subtitle")}</p>
        </div>
        <button
          onClick={handlePrint}
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition hover:bg-[var(--bg-tertiary)]"
          style={{
            borderColor: "var(--border-default)",
            background: "var(--bg-primary)",
            color: "var(--text-primary)",
          }}
        >
          <Download className="h-3.5 w-3.5" />
          {t("common.export")}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label={t("analytics.revenue")}
          value={formatCurrency(revenue.total_booked)}
          trend={{
            direction: revenue.growth_percent >= 0 ? "up" : "down",
            percentage: Math.abs(revenue.growth_percent),
          }}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          label={t("analytics.pipeline")}
          value={formatCurrency(pipeline.total_value)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          label={t("analytics.conversion")}
          value={`${conversionRate}%`}
          trend={
            pipeline.win_rate >= conversionRate
              ? {
                  direction: "up",
                  percentage: Math.abs(pipeline.win_rate - conversionRate),
                }
              : undefined
          }
          icon={<Target className="h-4 w-4" />}
        />
        <MetricCard
          label={t("analytics.avg_deal_size")}
          value={formatCurrency(pipeline.avg_deal_size)}
          icon={<BarChart3 className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.pipeline_stages")}
            </h3>
          </CardHeader>
          <CardContent>
            {pipelineStageData.length > 0 ? (
              <BarChart data={pipelineStageData} height={250} />
            ) : (
              <p className="text-xs text-[var(--text-muted)] text-center py-8">
                {t("analytics.no_data")}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.total_deals")}
            </h3>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3 mb-4">
              <Badge variant="success">
                {t("analytics.won_deals")}: {pipeline.won_deals}
              </Badge>
              <Badge variant="danger">
                {t("analytics.lost_deals")}: {pipeline.lost_deals}
              </Badge>
              <Badge variant="outline">
                {t("analytics.total_deals")}: {pipeline.total_deals}
              </Badge>
            </div>
            <PieChart data={wonLostData} height={200} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.growth")}
            </h3>
          </CardHeader>
          <CardContent>
            <BarChart data={growthData} height={250} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-[var(--muhide-orange)]" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                {t("analytics.risk_overview")}
              </h3>
            </div>
          </CardHeader>
          <CardContent>
            {riskData.some((d) => d.value > 0) ? (
              <BarChart data={riskData} height={200} />
            ) : (
              <div className="flex items-center justify-center h-[200px]">
                <Badge variant="success">{t("analytics.no_data")}</Badge>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[var(--muhide-orange)]" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                {t("analytics.team_overview")}
              </h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">
                  {t("analytics.active_employees")}
                </span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {team.active_employees} / {team.total_employees}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">{t("analytics.win_rate")}</span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {team.avg_win_rate}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-[var(--muhide-orange)]" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                {t("analytics.renewals")}
              </h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">
                  {t("analytics.due_30_days")}
                </span>
                <Badge variant="warning">{renewals.due_next_30_days}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">
                  {t("analytics.due_90_days")}
                </span>
                <Badge variant="outline">{renewals.due_next_90_days}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">
                  {t("analytics.renewal_value")}
                </span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {formatCurrency(renewals.total_renewal_value)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.forecast")}
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">{t("analytics.actual")}</span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {formatCurrency(revenue.total_booked)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">{t("analytics.forecast")}</span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {formatCurrency(revenue.forecast)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-muted)]">{t("analytics.weighted")}</span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  {formatCurrency(revenue.weighted_pipeline)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
