"use client";

import { cn } from "@salesos/ui";
import {
  Users,
  Activity,
  DollarSign,
  Target,
  Search,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import type { AnalyticsData } from "./types";

interface AnalyticsViewProps {
  data: AnalyticsData;
}

function MetricCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg",
            color ?? "bg-[var(--bg-tertiary)]",
          )}
        >
          {icon}
        </div>
        <div>
          <p className="text-xs text-[var(--text-muted)]">{label}</p>
          <p className="text-xl font-bold text-[var(--text-primary)]">
            {value}
          </p>
          {sub && <p className="text-[10px] text-[var(--text-muted)]">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

export function AnalyticsView({ data }: AnalyticsViewProps) {
  const { t } = useTranslation();
  const isEmpty =
    data.users.total === 0 &&
    data.pipeline.dealCount === 0 &&
    data.widgets.usageCount === 0 &&
    data.search.totalQueries === 0 &&
    data.nba.shown === 0;
  return (
    <div
      role="region"
      aria-label={t("analytics.title")}
      className="space-y-4 p-6"
    >
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">
          {t("analytics.title")}
        </h1>
        <p className="text-sm text-[var(--text-muted)]">
          {t("analytics.subtitle")}
        </p>
        {isEmpty && (
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            No live commercial analytics yet — zeros are honest; nothing is
            invented.
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <MetricCard
          icon={<Users className="h-4 w-4 text-blue-600" />}
          label={t("analytics.active_users")}
          value={data.users.active.toString()}
          sub={t("analytics.of_total", { total: data.users.total })}
          color="bg-blue-50 dark:bg-blue-900/20"
        />
        <MetricCard
          icon={
            <Activity className="h-4 w-4 text-[var(--status-success-text)]" />
          }
          label={t("analytics.daily_sessions")}
          value={data.usage.dailyActiveUsers.toString()}
          sub={t("analytics.avg_duration", {
            minutes: Math.round(data.usage.avgSessionDuration / 60),
          })}
          color="bg-[var(--status-success-bg)]"
        />
        <MetricCard
          icon={
            <DollarSign className="h-4 w-4 text-[var(--status-warning-text)]" />
          }
          label={t("analytics.pipeline_value")}
          value={`$${data.pipeline.totalValue >= 1e6 ? (data.pipeline.totalValue / 1e6).toFixed(1) + "M" : (data.pipeline.totalValue / 1e3).toFixed(0) + "K"}`}
          sub={t("analytics.deal_count", { count: data.pipeline.dealCount })}
          color="bg-[var(--status-warning-bg)]"
        />
        <MetricCard
          icon={<Target className="h-4 w-4 text-[var(--chart-purple)]" />}
          label={t("analytics.win_rate")}
          value={`%${Math.round(data.pipeline.winRate * 100)}`}
          sub={`${t("executive.weighted")} $${data.pipeline.weightedValue >= 1e6 ? (data.pipeline.weightedValue / 1e6).toFixed(1) + "M" : (data.pipeline.weightedValue / 1e3).toFixed(0) + "K"}`}
          color="bg-[var(--chart-purple-bg)] dark:bg-[var(--bg-primary)]/20"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Widget Usage */}
        <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] p-4">
          <div className="mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.most_used_widgets")}
            </span>
          </div>
          <div className="space-y-1.5">
            {data.widgets.widgets.slice(0, 6).map((w) => (
              <div key={w.id} className="flex items-center gap-2">
                <span className="w-24 truncate text-xs text-[var(--text-muted)]">
                  {w.name}
                </span>
                <div className="flex-1 h-4 rounded-lg bg-[var(--bg-tertiary)] overflow-hidden">
                  <div
                    className="h-full rounded-lg bg-primary-500"
                    style={{
                      width: `${(w.count / data.widgets.usageCount) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-10 text-right text-[10px] text-[var(--text-muted)]">
                  {w.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Search Analytics */}
        <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] p-4">
          <div className="mb-3 flex items-center gap-2">
            <Search className="h-4 w-4 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {t("analytics.search_analytics")}
            </span>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-[var(--text-muted)]">
                {t("analytics.total_queries")}
              </p>
              <p className="text-lg font-bold text-[var(--text-primary)]">
                {data.search.totalQueries.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)]">
                {t("analytics.avg_results")}
              </p>
              <p className="text-lg font-bold text-[var(--text-primary)]">
                {data.search.avgResults}
              </p>
            </div>
            <div>
              <p className="mb-1 text-xs text-[var(--text-muted)]">
                {t("analytics.top_queries")}
              </p>
              {data.search.topQueries.slice(0, 3).map((q, i) => (
                <p key={i} className="text-[10px] text-[var(--text-muted)]">
                  {i + 1}. {q}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* NBA Analytics */}
        <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] p-4">
          <div className="mb-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              NBA Analytics
            </span>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-[var(--text-muted)]">
                {t("analytics.shown_recommendations")}
              </p>
              <p className="text-lg font-bold text-[var(--text-primary)]">
                {data.nba.shown}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)]">
                {t("analytics.executed_recommendations")}
              </p>
              <p className="text-lg font-bold text-[var(--status-success-text)]">
                {data.nba.executed}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--text-muted)]">
                {t("analytics.acceptance_rate")}
              </p>
              <div className="mt-1 h-3 w-full rounded-full bg-[var(--bg-tertiary)]">
                <div
                  className={cn(
                    "h-full rounded-full",
                    data.nba.acceptanceRate >= 40
                      ? "bg-green-500"
                      : data.nba.acceptanceRate >= 20
                        ? "bg-amber-500"
                        : "bg-red-500",
                  )}
                  style={{ width: `${data.nba.acceptanceRate}%` }}
                />
              </div>
              <p className="mt-0.5 text-[10px] text-[var(--text-muted)]">
                %{data.nba.acceptanceRate}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
