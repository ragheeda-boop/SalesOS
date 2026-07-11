'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { MarketPulseViewProps } from './types'

const DIRECTION_CONFIG = {
  up: { icon: '↑', color: 'text-emerald-600 dark:text-emerald-400', label: 'صاعد' },
  down: { icon: '↓', color: 'text-danger-600 dark:text-danger-400', label: 'هابط' },
  stable: { icon: '→', color: 'text-neutral-500 dark:text-neutral-400', label: 'مستقر' },
} as const

function TrendRow({
  trend,
  onClick,
}: {
  trend: MarketPulseViewProps['trends'][number]
  onClick?: (name: string) => void
}) {
  const conf = DIRECTION_CONFIG[trend.direction]
  const handleClick = useCallback(() => onClick?.(trend.name), [trend.name, onClick])
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (onClick && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault()
        onClick(trend.name)
      }
    },
    [trend.name, onClick],
  )

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        onClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)] focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${trend.name} - ${conf.label} - ${trend.change}%`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-[var(--text-primary)]">{trend.name}</span>
          <span className="text-xs text-[var(--text-muted)]">{trend.description}</span>
        </div>
      </div>
      <span className={cn('shrink-0 text-sm font-medium', conf.color)}>
        <span aria-hidden="true">{conf.icon}</span> {trend.change}%
      </span>
    </div>
  )
}

function MoverRow({
  mover,
  onClick,
}: {
  mover: MarketPulseViewProps['topMovers'][number]
  onClick?: (companyId: string) => void
}) {
  const isPositive = mover.scoreChange >= 0
  const handleClick = useCallback(() => onClick?.(mover.companyId), [mover.companyId, onClick])
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (onClick && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault()
        onClick(mover.companyId)
      }
    },
    [mover.companyId, onClick],
  )

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        onClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)] focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${mover.companyName} - ${isPositive ? 'تحسن' : 'انخفاض'} ${Math.abs(mover.scoreChange)} نقطة`}
    >
      <div className="min-w-0 flex-1">
        <div className="font-medium text-[var(--text-primary)]">{mover.companyName}</div>
        <div className="mt-0.5 text-xs text-[var(--text-muted)]">{mover.reason}</div>
      </div>
      <span
        className={cn(
          'shrink-0 text-sm font-medium',
          isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-danger-600 dark:text-danger-400',
        )}
      >
        {isPositive ? '+' : ''}{mover.scoreChange}%
      </span>
    </div>
  )
}

export function MarketPulseView({ trends, topMovers, onTrendClick, onMoverClick }: MarketPulseViewProps) {
  if (trends.length === 0 && topMovers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">📊</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">بيانات السوق غير متاحة حالياً</p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">يمكنك المحاولة لاحقاً للحصول على أحدث البيانات</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="نبض السوق" className="space-y-4">
      {trends.length > 0 && (
        <div>
          <h3 className="mb-1 px-1 text-xs font-semibold text-[var(--text-muted)]">اتجاهات السوق</h3>
          <div role="list" aria-label="اتجاهات السوق" className="space-y-0.5">
            {trends.map((trend, i) => (
              <div role="listitem" key={`trend-${i}`}>
                <TrendRow trend={trend} onClick={onTrendClick} />
              </div>
            ))}
          </div>
        </div>
      )}

      {topMovers.length > 0 && (
        <div>
          <h3 className="mb-1 px-1 text-xs font-semibold text-[var(--text-muted)]">أبرز التحركات</h3>
          <div role="list" aria-label="أبرز التحركات" className="space-y-0.5">
            {topMovers.map((mover, i) => (
              <div role="listitem" key={`mover-${i}`}>
                <MoverRow mover={mover} onClick={onMoverClick} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
