'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { CompanyHealthViewProps, HealthMetric, HealthAlert } from './types'

const TREND_CONFIG = {
  up: { icon: '↑', color: 'text-emerald-600 dark:text-emerald-400', label: 'تحسن' },
  down: { icon: '↓', color: 'text-danger-600 dark:text-danger-400', label: 'انخفاض' },
  stable: { icon: '→', color: 'text-neutral-500 dark:text-neutral-400', label: 'مستقر' },
} as const

const ALERT_CONFIG = {
  critical: { bg: 'bg-danger-50 dark:bg-danger-900/10', border: 'border-danger-200 dark:border-danger-800', icon: '🔴', label: 'حرج' },
  warning: { bg: 'bg-warning-50 dark:bg-warning-900/10', border: 'border-warning-200 dark:border-warning-800', icon: '🟡', label: 'تحذير' },
  info: { bg: 'bg-info-50 dark:bg-info-900/10', border: 'border-info-200 dark:border-info-800', icon: '🔵', label: 'معلومات' },
} as const

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600 dark:text-emerald-400'
  if (score >= 60) return 'text-warning-600 dark:text-warning-400'
  return 'text-danger-600 dark:text-danger-400'
}

function getScoreRingColor(score: number): string {
  if (score >= 80) return 'border-emerald-500'
  if (score >= 60) return 'border-warning-500'
  return 'border-danger-500'
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  const circumference = 2 * Math.PI * 40
  const progress = (score / 100) * circumference

  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Overall score: ${score} out of 100`}>
      <svg width="100" height="100" viewBox="0 0 100 100" className="transform -rotate-90">
        <circle
          cx="50" cy="50" r="40"
          fill="none"
          stroke="var(--bg-tertiary, #e5e7eb)"
          strokeWidth="6"
        />
        <circle
          cx="50" cy="50" r="40"
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          className={cn(getScoreColor(score), 'transition-all duration-500 motion-reduce:transition-none')}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={cn('text-2xl font-bold', getScoreColor(score))}>{score}</span>
        <span className="text-[10px] text-[var(--text-muted)]">{label}</span>
      </div>
    </div>
  )
}

function MetricRow({
  metric,
  onClick,
}: {
  metric: HealthMetric
  onClick?: (id: string) => void
}) {
  const trend = TREND_CONFIG[metric.trend]
  const handleClick = useCallback(() => onClick?.(metric.id), [metric.id, onClick])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onClick(metric.id)
    }
  }, [metric.id, onClick])

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        onClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)] focus-visible:ring-offset-1',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${metric.label}: ${metric.value}${metric.unit} - ${trend.label} ${metric.trendValue}%`}
    >
      <div className="min-w-0 flex-1">
        <span className="font-medium text-[var(--text-primary)]">{metric.label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--text-secondary)]">
          {metric.value}{metric.unit}
        </span>
        <span className={cn('flex items-center gap-0.5 text-[10px] font-medium', trend.color)}>
          <span aria-hidden="true">{trend.icon}</span>
          {metric.trendValue}%
        </span>
      </div>
    </div>
  )
}

function AlertRow({
  alert,
  onClick,
}: {
  alert: HealthAlert
  onClick?: (id: string) => void
}) {
  const conf = ALERT_CONFIG[alert.type]
  const handleClick = useCallback(() => onClick?.(alert.id), [alert.id, onClick])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onClick(alert.id)
    }
  }, [alert.id, onClick])

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'flex items-start gap-2 rounded-lg border px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        conf.bg,
        conf.border,
        onClick && 'cursor-pointer hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)]',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${conf.label}: ${alert.message} - ${alert.companyName}`}
    >
      <span className="mt-0.5 shrink-0" aria-hidden="true">{conf.icon}</span>
      <div className="min-w-0 flex-1">
        <p className="text-[var(--text-primary)]">{alert.message}</p>
        <p className="mt-0.5 text-[10px] text-[var(--text-muted)]">{alert.companyName}</p>
      </div>
    </div>
  )
}

function SkeletonHealth() {
  return (
    <div className="space-y-4" role="status" aria-label="جاري تحميل بيانات الصحة">
      <div className="flex justify-center">
        <div className="h-[100px] w-[100px] animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-700" />
      </div>
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between rounded-lg px-3 py-2">
            <div className="h-3.5 w-24 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
            <div className="h-3.5 w-16 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function CompanyHealthView({
  overallScore,
  metrics,
  alerts,
  companyName,
  decision,
  nbaItems,
  isDecisionLoading,
  onAlertClick,
  onMetricClick,
}: CompanyHealthViewProps) {
  if (isDecisionLoading && metrics.length === 0) {
    return <SkeletonHealth />
  }

  if (metrics.length === 0 && alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">🏥</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">لا توجد بيانات صحة</p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">ستظهر بيانات صحة الشركة هنا</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label={`صحة الشركة: ${companyName}`} className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative">
          <ScoreRing score={overallScore} label="الصحة العامة" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">{companyName}</h3>
          <p className="text-xs text-[var(--text-muted)]">مؤشرات الأداء الرئيسية</p>
        </div>
      </div>

      {decision && (
        <div
          aria-live="polite"
          aria-atomic="true"
          className="rounded-lg bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-muted)]"
        >
          <span className="font-medium text-[var(--text-primary)]">تحليل AI: </span>
          {decision.summary}
        </div>
      )}

      <div>
        <div className="mb-1 px-1 text-xs font-semibold text-[var(--text-muted)]">مؤشرات الأداء</div>
        <div
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {metrics.length} مؤشر أداء — صحة عامة {overallScore} من 100
        </div>
        <div className="space-y-0.5">
          {metrics.map((metric) => (
            <MetricRow key={metric.id} metric={metric} onClick={onMetricClick} />
          ))}
        </div>
      </div>

      {alerts.length > 0 && (
        <div>
          <div className="mb-1 px-1 text-xs font-semibold text-[var(--text-muted)]">تنبيهات</div>
          <div className="space-y-1.5">
            {alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} onClick={onAlertClick} />
            ))}
          </div>
        </div>
      )}

      {nbaItems && nbaItems.length > 0 && (
        <div className="border-t border-[var(--border-secondary)] pt-2">
          <div className="mb-1 text-[10px] font-semibold text-[var(--text-muted)]">توصيات AI</div>
          {nbaItems.slice(0, 2).map((nba) => (
            <div
              key={nba.id}
              className="rounded-md px-2 py-1 text-xs text-[var(--text-muted)]"
              aria-label={`AI توصية: ${nba.action} لـ ${nba.company_name}`}
            >
              <span className="font-medium text-[var(--text-primary)]">{nba.company_name}</span>
              {' — '}
              {nba.action}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
