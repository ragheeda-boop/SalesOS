"use client"

import { useEmployeeScore } from "@/lib/hooks/employeeQueries"
import { useDecisionScores } from "@/lib/decisionQueries"
import { Card, CardContent, CardHeader, Skeleton, EmptyState, Badge } from "@salesos/ui"
import { Brain, BarChart3, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { useTranslation } from "@/lib/i18n"
import { ErrorFallback } from "@/components/foundation/error-boundary"
import type { Score } from "@salesos/decision-platform"

export function EmployeeScoring({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data: decisionScores, isLoading: dpLoading } = useDecisionScores(employeeId, 'employee')
  const { data: scoreData, isLoading: domainLoading, isError, error, refetch } = useEmployeeScore(employeeId)

  const isLoading = dpLoading && domainLoading

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl md:col-span-2" />
      </div>
    )
  }

  if (isError && (!decisionScores || decisionScores.length === 0)) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.score_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  const hasDpScores = decisionScores && decisionScores.length > 0
  const hasDomainScore = scoreData !== null && scoreData !== undefined

  if (!hasDpScores && !hasDomainScore) {
    return (
      <div className="py-12">
        <EmptyState icon={<Brain className="h-10 w-10" />} title={t("emp360.no_score")} description={t("emp360.no_score_hint")} />
      </div>
    )
  }

  const gaugeScore = hasDomainScore
    ? scoreData.score
    : Math.round(decisionScores!.reduce((sum: number, s: Score) => sum + (typeof s.value === 'number' ? s.value : 0), 0) / decisionScores!.length * 100)
  const gaugeColor = gaugeScore >= 70 ? "stroke-success-500" : gaugeScore >= 40 ? "stroke-warning-500" : "stroke-danger-500"
  const trendIcon = hasDomainScore ? (
    scoreData.trend === "up" ? <TrendingUp className="h-4 w-4 text-success-500" /> :
      scoreData.trend === "down" ? <TrendingDown className="h-4 w-4 text-danger-500" /> :
        <Minus className="h-4 w-4 text-[var(--text-disabled)]" />
  ) : <Minus className="h-4 w-4 text-[var(--text-disabled)]" />

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <Card className="flex flex-col items-center justify-center">
        <CardContent className="py-6">
          <div className="relative mb-3">
            <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-[var(--text-primary)]" />
              <circle cx="50" cy="50" r="42" fill="none" strokeWidth="8" strokeLinecap="round" className={gaugeColor} strokeDasharray={`${(gaugeScore / 100) * 263.9} 263.9`} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-[var(--text-primary)]">{gaugeScore}</span>
              <span className="text-[10px] text-[var(--text-muted)]">{t("emp360.out_of_100")}</span>
            </div>
          </div>
          {hasDomainScore && (
            <>
              <div className="flex items-center justify-center gap-1.5 text-sm">
                <span className="text-[var(--text-muted)]">{t("emp360.trend")}:</span>
                {trendIcon}
                <span className="text-xs text-[var(--text-disabled)] capitalize">{scoreData.trend}</span>
              </div>
              <div className="mt-4 flex items-center gap-2 text-xs">
                <span className="text-[var(--text-muted)]">{t("emp360.confidence")}:</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                  <div className="h-full rounded-full bg-info-500" style={{ width: `${scoreData.confidence}%` }} />
                </div>
                <span className="font-medium text-[var(--text-secondary)]">{Math.round(scoreData.confidence)}%</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            {hasDpScores ? (
              <>
                <Brain className="h-4 w-4 text-[var(--chart-purple)]" />
                <h3 className="text-sm font-semibold">{t("emp360.factors")}</h3>
                <Badge variant="primary" className="text-[10px]">Decision Platform</Badge>
              </>
            ) : (
              <>
                <BarChart3 className="h-4 w-4 text-[var(--text-muted)]" />
                <h3 className="text-sm font-semibold">{t("emp360.factors")}</h3>
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {hasDpScores ? (
              decisionScores.slice(0, 6).map((s: Score, i: number) => (
                <div key={s.name || String(i)}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-secondary)]">{s.label || s.name}</span>
                    <span className="font-medium text-[var(--text-primary)]">{Math.round((typeof s.value === 'number' ? s.value : 0) * 100)}%</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, (typeof s.value === 'number' ? s.value : 0) * 100)}%` }} />
                  </div>
                </div>
              ))
            ) : hasDomainScore ? (
              scoreData.factors.map((f) => (
                <div key={f.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-secondary)]">{f.label}</span>
                    <span className="font-medium text-[var(--text-primary)]">+{f.contribution}</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                    <div className="h-full rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, f.contribution * 5)}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-[var(--text-disabled)]">{t("emp360.no_factors")}</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
