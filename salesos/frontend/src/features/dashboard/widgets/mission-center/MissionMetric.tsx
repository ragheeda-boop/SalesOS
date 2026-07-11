'use client'

import { cn } from '@salesos/ui'
import type { MissionMetricProps } from './types'

export function MissionMetric({ label, value, valueClassName, icon, trend, ariaLabel }: MissionMetricProps) {
  const trendIcon = trend?.direction === 'up' ? '↑' : trend?.direction === 'down' ? '↓' : '→'
  const trendColor = trend?.direction === 'up' ? 'text-success-600' : trend?.direction === 'down' ? 'text-danger-600' : 'text-neutral-400'

  return (
    <div
      role="region"
      aria-label={ariaLabel ?? label}
      className="rounded-lg bg-[var(--bg-secondary)] p-3 text-center"
    >
      {icon && <div className="mb-1 text-lg" aria-hidden="true">{icon}</div>}
      <div className={cn('text-2xl font-bold leading-tight', valueClassName ?? 'text-[var(--muhide-orange)]')}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="mt-0.5 text-xs font-medium text-[var(--text-muted)]">{label}</div>
      {trend && (
        <div className={cn('mt-1 inline-flex items-center gap-0.5 text-[10px]', trendColor)} aria-label={`${trend.direction} ${trend.value}%`}>
          <span aria-hidden="true">{trendIcon}</span>
          {trend.value}%
        </div>
      )}
    </div>
  )
}
