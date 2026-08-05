"use client";

import { useExecutiveDashboard } from "@/lib/hooks/executiveQueries";
import { Card, CardContent, CardHeader, Badge, cn } from "@salesos/ui";
import { formatNumber } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import {
  DollarSign,
  TrendingUp,
  Users,
  AlertTriangle,
  Activity,
  BarChart3,
  Target,
  Calendar,
  Building2,
  UserPlus,
  FileSignature,
  Shield,
  ArrowUp,
  ArrowDown,
} from "lucide-react";

function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
  trendUp,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  color: string;
  trend?: number;
  trendUp?: boolean;
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-[var(--text-muted)]">{title}</p>
            <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
            {subtitle && <p className="text-xs text-[var(--text-muted)]">{subtitle}</p>}
            {trend !== undefined && (
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 text-xs",
                  trendUp ? "text-success-600" : "text-danger-600"
                )}
              >
                {trendUp ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                {trend}%
              </span>
            )}
          </div>
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", color)}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProgressBar({
  value,
  max,
  label,
  color,
}: {
  value: number;
  max: number;
  label: string;
  color: string;
}) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--text-secondary)]">{label}</span>
        <span className="font-medium text-[var(--text-primary)]">{formatNumber(value)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ExecutiveDashboard() {
  const { t } = useTranslation();
  const { data, isLoading } = useExecutiveDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-5">
                <div className="h-20 animate-pulse rounded bg-[var(--bg-tertiary)]" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-[var(--text-muted)]">{t("common.load_error")}</p>
      </div>
    );
  }

  const d = data;
  const healthColor =
    d.health.overall_health === "good"
      ? "text-success-600 bg-success-100"
      : d.health.overall_health === "warning"
        ? "text-warning-600 bg-warning-100"
        : "text-danger-600 bg-danger-100";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("executive.title")}</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">{t("executive.subtitle")}</p>
        </div>
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium",
            healthColor
          )}
        >
          <Shield className="h-3 w-3" />
          {d.health.overall_health === "good"
            ? t("status.healthy")
            : d.health.overall_health === "warning"
              ? t("status.warning")
              : t("status.critical")}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title={t("executive.booked_revenue")}
          value={`${formatNumber(d.revenue.total_booked)} ${t("common.currency")}`}
          subtitle={`${t("executive.target")} ${formatNumber(d.revenue.forecast)} ${t("common.currency")}`}
          icon={DollarSign}
          color="bg-success-600"
        />
        <KPICard
          title={t("executive.deal_value")}
          value={`${formatNumber(d.revenue.total_pipeline)} ${t("common.currency")}`}
          subtitle={`${t("executive.weighted")} ${formatNumber(d.revenue.weighted_pipeline)} ${t("common.currency")}`}
          icon={TrendingUp}
          color="bg-info-600"
        />
        <KPICard
          title={t("executive.active_employees")}
          value={`${d.team.active_employees} / ${d.team.total_employees}`}
          subtitle={`${t("executive.win_rate")} ${Math.round(d.team.avg_win_rate * 100)}%`}
          icon={Users}
          color="bg-purple-600"
        />
        <KPICard
          title={t("executive.risks")}
          value={String(d.risk.expiring_contracts + d.risk.stalled_deals)}
          subtitle={`${t("executive.expiring_contracts")} ${d.risk.expiring_contracts} | ${t("executive.stalled_deals")} ${d.risk.stalled_deals}`}
          icon={AlertTriangle}
          color="bg-danger-600"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pipeline Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-info-600" />
              <h2 className="text-lg font-bold text-[var(--text-primary)]">
                {t("executive.deal_health")}
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-info-50 p-3 dark:bg-info-900/20">
                <p className="text-xs text-info-600 dark:text-info-400">
                  {t("executive.total_deals")}
                </p>
                <p className="text-xl font-bold text-[var(--text-primary)]">
                  {d.pipeline.total_deals}
                </p>
              </div>
              <div className="rounded-lg bg-success-50 p-3 dark:bg-success-900/20">
                <p className="text-xs text-success-600 dark:text-success-400">
                  {t("executive.won_deals")}
                </p>
                <p className="text-xl font-bold text-[var(--text-primary)]">
                  {d.pipeline.won_deals}
                </p>
              </div>
              <div className="rounded-lg bg-danger-50 p-3 dark:bg-danger-900/20">
                <p className="text-xs text-danger-600 dark:text-danger-400">
                  {t("executive.lost_deals")}
                </p>
                <p className="text-xl font-bold text-[var(--text-primary)]">
                  {d.pipeline.lost_deals}
                </p>
              </div>
              <div className="rounded-lg bg-warning-50 p-3 dark:bg-warning-900/20">
                <p className="text-xs text-warning-600 dark:text-warning-400">
                  {t("executive.win_rate_short")}
                </p>
                <p className="text-xl font-bold text-[var(--text-primary)]">
                  {Math.round(d.pipeline.win_rate * 100)}%
                </p>
              </div>
            </div>

            {d.pipeline.by_stage.length > 0 && (
              <div className="space-y-3 pt-2">
                <h3 className="text-sm font-medium text-[var(--text-secondary)]">
                  {t("executive.by_stage")}
                </h3>
                {d.pipeline.by_stage.map((stage) => (
                  <ProgressBar
                    key={stage.stage}
                    label={stage.stage}
                    value={stage.val}
                    max={d.pipeline.total_value}
                    color="bg-info-500"
                  />
                ))}
              </div>
            )}

            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--text-secondary)]">{t("executive.avg_deal_size")}</span>
                <span className="font-bold text-[var(--text-primary)]">
                  {formatNumber(d.pipeline.avg_deal_size)} {t("common.currency")}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Growth & Renewals */}
        <div className="space-y-6">
          {/* Growth */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-success-600" />
                <h2 className="text-lg font-bold text-[var(--text-primary)]">
                  {t("executive.growth_30d")}
                </h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-info-100 dark:bg-info-900/50">
                    <Building2 className="h-5 w-5 text-info-600 dark:text-info-400" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-muted)]">
                      {t("executive.new_companies")}
                    </p>
                    <p className="text-lg font-bold text-[var(--text-primary)]">
                      {d.growth.new_companies_30d}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-100 dark:bg-success-900/50">
                    <UserPlus className="h-5 w-5 text-success-600 dark:text-success-400" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-muted)]">
                      {t("executive.new_contacts")}
                    </p>
                    <p className="text-lg font-bold text-[var(--text-primary)]">
                      {d.growth.new_contacts_30d}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning-100 dark:bg-warning-900/50">
                    <Target className="h-5 w-5 text-warning-600 dark:text-warning-400" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-muted)]">
                      {t("executive.new_opportunities")}
                    </p>
                    <p className="text-lg font-bold text-[var(--text-primary)]">
                      {d.growth.new_opportunities_30d}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--chart-purple-bg)] dark:bg-[var(--bg-primary)]/50">
                    <FileSignature className="h-5 w-5 text-[var(--chart-purple)] dark:text-[var(--chart-purple)]" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-muted)]">
                      {t("executive.new_contracts")}
                    </p>
                    <p className="text-lg font-bold text-[var(--text-primary)]">
                      {d.growth.new_contracts_30d}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Renewals */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-orange-600" />
                <h2 className="text-lg font-bold text-[var(--text-primary)]">
                  {t("executive.renewals")}
                </h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-orange-50 p-4 text-center dark:bg-orange-900/20">
                  <p className="text-xs text-orange-600 dark:text-orange-400">
                    {t("executive.due_30d")}
                  </p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {d.renewals.due_next_30_days}
                  </p>
                </div>
                <div className="rounded-lg bg-warning-50 p-4 text-center dark:bg-warning-900/20">
                  <p className="text-xs text-warning-600 dark:text-warning-400">
                    {t("executive.due_90d")}
                  </p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {d.renewals.due_next_90_days}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Health Footer */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-[var(--text-muted)]" />
              <span className="text-[var(--text-secondary)]">{t("executive.sync_status")}</span>
              <Badge variant={d.health.sync_status === "synced" ? "success" : "warning"}>
                {d.health.sync_status === "synced" ? t("status.synced") : t("status.unsynced")}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-secondary)]">
                {t("executive.data_completeness")}
              </span>
              <span className="font-medium text-[var(--text-primary)]">
                {Math.round(d.health.data_completeness * 100)}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
