"use client"

import { useEmployeePerformance } from "@/lib/hooks/employeeQueries"
import { Card, CardContent, CardHeader, Skeleton, EmptyState, Badge, cn } from "@salesos/ui"
import { TrendingUp, TrendingDown, Minus, Users, Shield, BarChart3, CheckCircle, AlertTriangle, Target } from "lucide-react"
import { useTranslation } from "@/lib/i18n"
import { ErrorFallback } from "@/components/foundation/error-boundary"

export function EmployeePerformance({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data: performance, isLoading, isError, error, refetch } = useEmployeePerformance(employeeId)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.performance_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  if (!performance) {
    return (
      <div className="py-12">
        <EmptyState icon={<TrendingUp className="h-10 w-10" />} title={t("emp360.no_performance")} description={t("emp360.no_performance_hint")} />
      </div>
    )
  }

  const maxScore = Math.max(...performance.score_trend.map((p: { score: number }) => p.score), 100)
  const trendDirIcon = performance.score_trend_direction === "up" ? <TrendingUp className="h-4 w-4 text-success-500" /> :
    performance.score_trend_direction === "down" ? <TrendingDown className="h-4 w-4 text-danger-500" /> :
      <Minus className="h-4 w-4 text-[var(--text-disabled)]" />

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-success-600" />
                <h3 className="text-sm font-semibold">{t("emp360.score_trend")}</h3>
              </div>
              <div className="flex items-center gap-1 text-sm">
                {trendDirIcon}
                <span className="text-xs text-[var(--text-disabled)] capitalize">{performance.score_trend_direction}</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {performance.score_trend.length === 0 ? (
              <p className="text-xs text-[var(--text-disabled)] text-center py-8">{t("emp360.no_trend_data")}</p>
            ) : (
              <div className="relative h-48 w-full">
                <svg className="h-full w-full" viewBox="0 0 400 150" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="trend-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="var(--muhide-orange)" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="var(--muhide-orange)" stopOpacity="0.02" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M0,${150 - (performance.score_trend[0]?.score || 0) / maxScore * 140} ${performance.score_trend.map((p: { score: number }, i: number) => `L${(i / Math.max(1, performance.score_trend.length - 1)) * 400},${150 - p.score / maxScore * 140}`).join(" ")} L400,150 L0,150 Z`}
                    fill="url(#trend-gradient)"
                  />
                  <polyline
                    points={performance.score_trend.map((p: { score: number }, i: number) => `${(i / Math.max(1, performance.score_trend.length - 1)) * 400},${150 - p.score / maxScore * 140}`).join(" ")}
                    fill="none"
                    stroke="var(--muhide-orange)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {performance.score_trend.map((p: { score: number }, i: number) => (
                    <circle
                      key={i}
                      cx={(i / Math.max(1, performance.score_trend.length - 1)) * 400}
                      cy={150 - p.score / maxScore * 140}
                      r="3"
                      fill="var(--muhide-orange)"
                    />
                  ))}
                </svg>
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-[var(--text-disabled)]">
                  <span>{performance.score_trend[0]?.date}</span>
                  <span>{performance.score_trend[performance.score_trend.length - 1]?.date}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[var(--chart-purple)]" />
              <h3 className="text-sm font-semibold">{t("emp360.peer_comparison")}</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {performance.peer_comparison.map((p: { metric: string; employee_value: number; department_avg: number; label: string }) => {
                const maxVal = Math.max(p.employee_value, p.department_avg, 1)
                return (
                  <div key={p.metric}>
                    <p className="mb-1.5 text-xs font-medium text-[var(--text-secondary)]">{p.label}</p>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="w-16 text-[10px] text-[var(--text-muted)]">{t("emp360.you")}</span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                          <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${(p.employee_value / maxVal) * 100}%` }} />
                        </div>
                        <span className="w-8 text-right text-[10px] font-medium text-[var(--text-primary)]">{Math.round(p.employee_value)}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="w-16 text-[10px] text-[var(--text-muted)]">{t("emp360.dept_avg")}</span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                          <div className="h-full rounded-full bg-neutral-400" style={{ width: `${(p.department_avg / maxVal) * 100}%` }} />
                        </div>
                        <span className="w-8 text-right text-[10px] font-medium text-[var(--text-primary)]">{Math.round(p.department_avg)}%</span>
                      </div>
                    </div>
                  </div>
                )
              })}
              {performance.peer_comparison.length === 0 && (
                <p className="text-xs text-[var(--text-disabled)] text-center py-4">{t("emp360.no_comparison")}</p>
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
              {performance.risk_flags.map((flag: { type: string; label: string; severity: "high" | "medium" | "low"; description: string }) => {
                const severityConfig = {
                  high: { bg: "bg-danger-50 dark:bg-danger-900/20", border: "border-danger-200 dark:border-danger-800", icon: <AlertTriangle className="h-4 w-4 text-danger-600" />, badge: "danger" as const },
                  medium: { bg: "bg-warning-50 dark:bg-warning-900/20", border: "border-warning-200 dark:border-warning-800", icon: <Target className="h-4 w-4 text-warning-600" />, badge: "warning" as const },
                  low: { bg: "bg-success-50 dark:bg-success-900/20", border: "border-success-200 dark:border-success-800", icon: <CheckCircle className="h-4 w-4 text-success-600" />, badge: "success" as const },
                }
                const cfg = severityConfig[flag.severity]
                return (
                  <div key={flag.type} className={cn("flex items-start gap-3 rounded-lg border p-3", cfg.bg, cfg.border)}>
                    {cfg.icon}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">{flag.label}</span>
                        <Badge variant={cfg.badge} className="text-[10px]">{flag.severity}</Badge>
                      </div>
                      <p className="mt-0.5 text-xs text-[var(--text-secondary)]">{flag.description}</p>
                    </div>
                  </div>
                )
              })}
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
              {performance.factors.map((f: { name: string; contribution: number; label: string }) => (
                <div key={f.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-secondary)]">{f.label}</span>
                    <span className="font-medium text-[var(--text-primary)]">+{f.contribution}</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, f.contribution * 5)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
