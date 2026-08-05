"use client";

import { Card, CardContent, EmptyState as UiEmptyState } from "@salesos/ui";
import { AlertTriangle, TrendingUp, Building2 } from "lucide-react";
import { MissionMetric } from "./MissionMetric";
import { MissionAction } from "./MissionAction";
import { MissionProgress } from "./MissionProgress";
import { useTranslation } from "@/lib/i18n";
import type { MissionCenterViewProps } from "./types";

function deriveActions(
  props: MissionCenterViewProps,
  t: (key: string, params?: Record<string, string | number>) => string
) {
  const actions: {
    id: string;
    title: string;
    priority: "high" | "medium" | "low";
    companyName?: string;
  }[] = [];

  if (props.signalsToday > 0) {
    actions.push({
      id: "review-signals",
      title: t("mission.action.review_signals", { count: props.signalsToday }),
      priority: "high",
    });
  }

  if (props.decisionsPending > 0) {
    actions.push({
      id: "pending-decisions",
      title: t("mission.action.pending_decisions", {
        count: props.decisionsPending,
      }),
      priority: "high",
    });
  }

  if (props.activeDeals > 0) {
    actions.push({
      id: "active-deals",
      title: t("mission.action.follow_deals", { count: props.activeDeals }),
      priority: "medium",
    });
  }

  if (props.companiesTracked > 10) {
    actions.push({
      id: "new-companies",
      title: t("mission.action.review_companies", {
        count: props.companiesTracked,
      }),
      priority: "low",
    });
  }

  return actions.slice(0, 5);
}

function EmptyStatePlaceholder() {
  const { t } = useTranslation();
  return (
    <UiEmptyState
      icon={<Building2 className="h-8 w-8" />}
      title={t("mission.empty.title")}
      description={t("mission.empty.hint")}
    />
  );
}

function SummaryBanner({ metrics }: { metrics: { label: string; value: number }[] }) {
  const { t } = useTranslation();
  const activeMetrics = metrics.filter((m) => m.value > 0);
  return (
    <div className="text-xs text-[var(--text-muted)]" aria-live="polite" aria-atomic="true">
      {activeMetrics.length > 0
        ? `${activeMetrics.map((m) => `${m.value} ${m.label}`).join("، ")}`
        : t("mission.summary.no_metrics")}
    </div>
  );
}

export function MissionCenterView(props: MissionCenterViewProps) {
  const { t } = useTranslation();
  const isAllZero =
    props.companiesTracked === 0 &&
    props.activeDeals === 0 &&
    props.pipelineValue === 0 &&
    props.signalsToday === 0 &&
    props.decisionsPending === 0;
  const actions = !isAllZero ? deriveActions(props, t) : [];

  if (isAllZero) {
    return (
      <div className="flex flex-col gap-4" role="region" aria-label="Mission Center Dashboard">
        <SummaryBanner
          metrics={[
            {
              label: t("mission.companies_short"),
              value: props.companiesTracked,
            },
            { label: t("mission.deals_short"), value: props.activeDeals },
            { label: t("mission.signals_short"), value: props.signalsToday },
          ]}
        />
        <EmptyStatePlaceholder />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4" role="region" aria-label="Mission Center Dashboard">
      <SummaryBanner
        metrics={[
          {
            label: t("mission.companies_short"),
            value: props.companiesTracked,
          },
          { label: t("mission.deals_short"), value: props.activeDeals },
          { label: t("mission.signals_short"), value: props.signalsToday },
        ]}
      />

      {/* Metrics Grid */}
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))" }}
        role="list"
        aria-label="Key metrics"
      >
        <div role="listitem">
          <MissionMetric
            label={t("dashboard.metrics.companies_tracked")}
            value={props.companiesTracked}
            valueClassName="text-info-600 dark:text-info-400"
            ariaLabel={t("mission.aria.companies_tracked", {
              count: props.companiesTracked,
            })}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label={t("dashboard.metrics.active_deals")}
            value={props.activeDeals}
            valueClassName="text-[var(--muhide-orange)]"
            ariaLabel={t("mission.aria.active_deals", {
              count: props.activeDeals,
            })}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label={t("dashboard.metrics.pipeline_value")}
            value={`${(props.pipelineValue / 1000000).toFixed(1)}M`}
            valueClassName="text-success-600 dark:text-success-400"
            ariaLabel={t("mission.aria.pipeline_value", {
              value: props.pipelineValue.toLocaleString(),
            })}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label={t("dashboard.metrics.signals_today")}
            value={props.signalsToday}
            valueClassName="text-info-600 dark:text-info-400"
            icon="📡"
            ariaLabel={t("mission.aria.signals_today", {
              count: props.signalsToday,
            })}
          />
        </div>
        <div role="listitem">
          <MissionMetric
            label={t("dashboard.metrics.decisions_pending")}
            value={props.decisionsPending}
            valueClassName="text-danger-600 dark:text-danger-400"
            icon="⚡"
            ariaLabel={t("mission.aria.decisions_pending", {
              count: props.decisionsPending,
            })}
          />
        </div>
      </div>

      {/* Priority Actions */}
      {actions.length > 0 && (
        <Card className="border-0 shadow-none bg-[var(--bg-secondary)]">
          <CardContent className="p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <AlertTriangle className="h-3.5 w-3.5 text-warning-500" aria-hidden="true" />
              <span className="text-xs font-semibold text-[var(--text-primary)]">Priorities</span>
            </div>
            <div className="flex flex-col gap-1.5" role="list" aria-label="Priority actions">
              {actions.map((action) => (
                <div key={action.id} role="listitem">
                  <MissionAction
                    id={action.id}
                    title={action.title}
                    priority={action.priority}
                    companyName={action.companyName}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Revenue & Progress row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Card className="border-0 shadow-none bg-gradient-to-br from-success-50 to-emerald-50 dark:from-success-950/30 dark:to-emerald-950/30">
          <CardContent className="p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className="h-3.5 w-3.5 text-success-600" aria-hidden="true" />
              <span className="text-xs font-semibold text-success-700 dark:text-success-300">
                Revenue Opportunity
              </span>
            </div>
            <p className="text-lg font-bold text-success-800 dark:text-success-200">
              SAR {props.pipelineValue.toLocaleString()}
            </p>
            <p className="text-[10px] text-success-600 dark:text-success-400">
              {props.activeDeals} {t("dashboard.metrics.active_deals")}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-none bg-[var(--bg-secondary)]">
          <CardContent className="p-3">
            <MissionProgress
              value={props.activeDeals * 2 + props.signalsToday + props.decisionsPending}
              max={100}
              label="Completion"
              barClassName="bg-[var(--muhide-orange)]"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
