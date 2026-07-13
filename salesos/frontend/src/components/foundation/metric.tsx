import { cn } from "@salesos/ui"
import { Typography } from "./typography"

interface MetricProps {
  value: string | number
  label: string
  trend?: 'up' | 'down' | 'flat'
  trendValue?: string
  icon?: React.ReactNode
  color?: 'default' | 'brand' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  className?: string
}

const COLOR_VALUES = {
  default: 'text-[var(--text-primary)]',
  brand: 'text-[var(--muhide-orange)]',
  success: 'text-success-600',
  warning: 'text-warning-600',
  danger: 'text-danger-600',
}

const TREND_ICONS = {
  up: '↑',
  down: '↓',
  flat: '→',
}

const TREND_COLORS = {
  up: 'text-success-600',
  down: 'text-danger-600',
  flat: 'text-[var(--text-muted)]',
}

const SIZE_VALUES = {
  sm: 'text-xl',
  md: 'text-2xl',
  lg: 'text-3xl',
}

export function Metric({ value, label, trend, trendValue, icon, color = 'default', size = 'md', loading, className }: MetricProps) {
  if (loading) {
    return (
      <div className={cn('flex flex-col gap-1 p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-default)]', className)} aria-busy="true" role="status">
        <div className="h-3 w-20 bg-neutral-200 rounded animate-pulse" aria-hidden="true" />
        <div className="h-8 w-24 bg-neutral-200 rounded animate-pulse" aria-hidden="true" />
        {trend && <div className="h-3 w-16 bg-neutral-200 rounded animate-pulse" aria-hidden="true" />}
      </div>
    )
  }

  const trendLabel = trend === 'up' ? 'Increased' : trend === 'down' ? 'Decreased' : 'No change'

  return (
    <div className={cn('flex flex-col gap-1 p-4 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-default)]', className)}>
      <div className="flex items-center justify-between">
        <Typography variant="caption" color="muted">{label}</Typography>
        {icon && <span className="text-[var(--text-muted)]">{icon}</span>}
      </div>
      <Typography variant="h3" as="div" className={cn(SIZE_VALUES[size], COLOR_VALUES[color], 'font-display')}>
        {value}
      </Typography>
      {trend && (
        <div className="flex items-center gap-1">
          <span className={cn('text-sm', TREND_COLORS[trend])} aria-hidden="true">{TREND_ICONS[trend]}</span>
          <span className="sr-only">{trendLabel}</span>
          {trendValue && <Typography variant="caption" color="muted">{trendValue}</Typography>}
        </div>
      )}
    </div>
  )
}
