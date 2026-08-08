"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEmployeePerformance } from "@/lib/hooks/employeeQueries";
import { Card, CardContent, CardHeader, Skeleton, EmptyState, Badge, cn } from "@salesos/ui";
import {
  TrendingUp,
  Users,
  Shield,
  BarChart3,
  CheckCircle,
  AlertTriangle,
  Target,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { ErrorFallback } from "@/components/foundation/error-boundary";
import { TrendChart } from "./employee-360-trend-chart";

export function EmployeePerformance({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation();
  const {
    data: performance,
    isLoading,
    isError,
    error,
    refetch,
  } = useEmployeePerformance(employeeId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback
          title={t("emp360.performance_error")}
          message={(error as Error)?.message}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (!performance) {
    return (
      <div className="py-12">
        <EmptyState
          icon={<TrendingUp className="h-10 w-10" />}
          title={t("emp360.no_performance")}
          description={t("emp360.no_performance_hint")}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <TrendChart data={performance.score_trend} direction={performance.score_trend_direction} />

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[var(--chart-purple)]" />
              <h3 className="text-sm font-semibold">{t("emp360.peer_comparison")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performance.peer_comparison.map(
                (p: {
                  metric: string;
                  employee_value: number;
                  department_avg: number;
                  label: string;
                }) => {
                  const maxVal = Math.max(p.employee_value, p.department_avg, 1);
                  return (
                    <div key={p.metric}>
                      <p className="mb-1.5 text-xs font-medium text-[var(--text-secondary)]">
                        {p.label}
                      </p>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="w-16 text-[10px] text-[var(--text-muted)]">
                            {t("emp360.you")}
                          </span>
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                            <div
                              className="h-full rounded-full bg-[var(--muhide-orange)]"
                              style={{
                                width: `${(p.employee_value / maxVal) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="w-8 text-end text-[10px] font-medium text-[var(--text-primary)]">
                            {Math.round(p.employee_value)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="w-16 text-[10px] text-[var(--text-muted)]">
                            {t("emp360.dept_avg")}
                          </span>
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                            <div
                              className="h-full rounded-full bg-neutral-400"
                              style={{
                                width: `${(p.department_avg / maxVal) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="w-8 text-end text-[10px] font-medium text-[var(--text-primary)]">
                            {Math.round(p.department_avg)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                }
              )}
              {performance.peer_comparison.length === 0 && (
                <p className="py-4 text-center text-xs text-[var(--text-disabled)]">
                  {t("emp360.no_comparison")}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {performance.risk_flags.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-warning-600" />
              <h3 className="text-sm font-semibold">{t("emp360.risk_flags")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {performance.risk_flags.map(
                (flag: {
                  type: string;
                  label: string;
                  severity: "high" | "medium" | "low";
                  description: string;
                }) => {
                  const severityConfig = {
                    high: {
                      bg: "bg-danger-50 dark:bg-danger-900/20",
                      border: "border-danger-200 dark:border-danger-800",
                      icon: <AlertTriangle className="h-4 w-4 text-danger-600" />,
                      badge: "danger" as const,
                    },
                    medium: {
                      bg: "bg-warning-50 dark:bg-warning-900/20",
                      border: "border-warning-200 dark:border-warning-800",
                      icon: <Target className="h-4 w-4 text-warning-600" />,
                      badge: "warning" as const,
                    },
                    low: {
                      bg: "bg-success-50 dark:bg-success-900/20",
                      border: "border-success-200 dark:border-success-800",
                      icon: <CheckCircle className="h-4 w-4 text-success-600" />,
                      badge: "success" as const,
                    },
                  };
                  const cfg = severityConfig[flag.severity];
                  return (
                    <div
                      key={flag.type}
                      className={cn(
                        "flex items-start gap-3 rounded-lg border p-3",
                        cfg.bg,
                        cfg.border
                      )}
                    >
                      {cfg.icon}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">
                            {flag.label}
                          </span>
                          <Badge variant={cfg.badge} className="text-[10px]">
                            {flag.severity}
                          </Badge>
                        </div>
                        <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                          {flag.description}
                        </p>
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {performance.factors.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-[var(--text-muted)]" />
              <h3 className="text-sm font-semibold">{t("emp360.factors_breakdown")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performance.factors.map(
                (f: { name: string; contribution: number; label: string }) => (
                  <div key={f.name}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">{f.label}</span>
                      <span className="font-medium text-[var(--text-primary)]">
                        +{f.contribution}
                      </span>
                    </div>
                    <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                      <div
                        className="h-full rounded-full bg-[var(--muhide-orange)]"
                        style={{
                          width: `${Math.min(100, f.contribution * 5)}%`,
                        }}
                      />
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
