"use client";

import Link from "next/link";
import {
  Building2,
  DollarSign,
  Activity,
  AlertCircle,
  TrendingUp,
  Search,
} from "lucide-react";
import { useDashboardContext } from "../_providers/dashboard-provider";
import { useTranslation } from "@/lib/i18n";
import type { MissionCenterData } from "@/application/dashboard/dashboard.dto";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  colorClass: string;
  ariaLabel: string;
}

function MetricCard({
  label,
  value,
  icon,
  colorClass,
  ariaLabel,
}: MetricCardProps) {
  return (
    <div
      role="region"
      aria-label={ariaLabel}
      className="rounded-xl border border-[var(--border-secondary)] bg-[var(--bg-primary)] p-4 transition-colors hover:border-[var(--border-interactive)]"
    >
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colorClass}`}>{icon}</div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-[var(--text-muted)] truncate">
            {label}
          </p>
          <p className="text-xl font-bold text-[var(--text-primary)] tabular-nums">
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
        </div>
      </div>
    </div>
  );
}

function QuickActions() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-2">
      <Link
        href="/companies/new"
        className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--muhide-orange)] px-3 py-2 text-xs font-semibold text-white transition-colors hover:opacity-90"
      >
        <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
        <span>{t("dashboard.new_company")}</span>
      </Link>
      <Link
        href="/search"
        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-secondary)] bg-[var(--bg-primary)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-secondary)]"
      >
        <Search className="h-3.5 w-3.5" aria-hidden="true" />
        <span>{t("common.search")}</span>
      </Link>
    </div>
  );
}

export function DashboardMetricsHeader() {
  const { widgets } = useDashboardContext();
  const { t } = useTranslation();
  const missionData = widgets.missionCenter?.data as MissionCenterData | null;

  if (!missionData) return null;

  const metrics: MetricCardProps[] = [
    {
      label: t("dashboard.metrics.companies_tracked"),
      value: missionData.companiesTracked,
      icon: <Building2 className="h-4 w-4 text-info-600 dark:text-info-400" />,
      colorClass: "bg-info-50 dark:bg-info-950/30",
      ariaLabel: t("mission.aria.companies_tracked", {
        count: missionData.companiesTracked,
      }),
    },
    {
      label: t("dashboard.metrics.active_deals"),
      value: missionData.activeDeals,
      icon: <DollarSign className="h-4 w-4 text-[var(--muhide-orange)]" />,
      colorClass: "bg-orange-50 dark:bg-orange-950/30",
      ariaLabel: t("mission.aria.active_deals", {
        count: missionData.activeDeals,
      }),
    },
    {
      label: t("dashboard.metrics.pipeline_value"),
      value:
        missionData.pipelineValue > 0
          ? `${(missionData.pipelineValue / 1_000_000).toFixed(1)}M`
          : "0",
      icon: (
        <TrendingUp className="h-4 w-4 text-success-600 dark:text-success-400" />
      ),
      colorClass: "bg-success-50 dark:bg-success-950/30",
      ariaLabel: t("mission.aria.pipeline_value", {
        value: missionData.pipelineValue.toLocaleString(),
      }),
    },
    {
      label: t("dashboard.metrics.signals_today"),
      value: missionData.signalsToday,
      icon: <Activity className="h-4 w-4 text-info-600 dark:text-info-400" />,
      colorClass: "bg-info-50 dark:bg-info-950/30",
      ariaLabel: t("mission.aria.signals_today", {
        count: missionData.signalsToday,
      }),
    },
    {
      label: t("dashboard.metrics.decisions_pending"),
      value: missionData.decisionsPending,
      icon: (
        <AlertCircle className="h-4 w-4 text-danger-600 dark:text-danger-400" />
      ),
      colorClass: "bg-danger-50 dark:bg-danger-950/30",
      ariaLabel: t("mission.aria.decisions_pending", {
        count: missionData.decisionsPending,
      }),
    },
  ];

  return (
    <div className="mb-6" role="region" aria-label={t("dashboard.summary")}>
      <div className="mb-4 flex items-center justify-end">
        <QuickActions />
      </div>
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}
        role="list"
        aria-label="Key metrics"
      >
        {metrics.map((metric) => (
          <div key={metric.label} role="listitem">
            <MetricCard {...metric} />
          </div>
        ))}
      </div>
    </div>
  );
}
