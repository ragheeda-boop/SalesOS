import { cn } from "@salesos/ui"

type BadgeVariant = 'status' | 'tier' | 'source' | 'doc-status' | 'intelligence-score' | 'default' | 'outline'
type BadgeSize = 'sm' | 'md'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  dot?: boolean
  value?: string | number
}

const SIZE_CLASSES = {
  sm: 'px-1.5 py-0.5 text-[10px]',
  md: 'px-2 py-0.5 text-xs',
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-success-100 text-success-800',
  evaluation: 'bg-warning-100 text-warning-800',
  negotiation: 'bg-info-100 text-info-800',
  pending: 'bg-neutral-100 text-neutral-600',
  signed: 'bg-success-100 text-success-800',
  confidential: 'bg-purple-100 text-purple-800',
}

const TIER_CLASSES = 'bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] font-medium'

const SOURCE_COLORS: Record<string, string> = {
  wathq: 'bg-orange-100 text-[var(--muhide-orange)]',
  balady: 'bg-success-100 text-success-700',
  najiz: 'bg-info-100 text-info-700',
  linkedin: 'bg-[#E8F0FE] text-[#0A66C2]',
  manual: 'bg-neutral-100 text-neutral-600',
}

function getScoreColor(score: number): string {
  if (score <= 30) return 'bg-danger-100 text-danger-700'
  if (score <= 60) return 'bg-warning-100 text-warning-700'
  if (score <= 80) return 'bg-success-100 text-success-700'
  return 'bg-emerald-100 text-emerald-700'
}

const DOT_CLASSES: Record<string, string> = {
  active: 'bg-success-500',
  evaluation: 'bg-warning-500',
  negotiation: 'bg-info-500',
  pending: 'bg-neutral-400',
  signed: 'bg-success-500',
  confidential: 'bg-purple-500',
}

export function Badge({ variant = 'default', size = 'md', dot, value, className, children, ...props }: BadgeProps) {
  const label = value ?? children
  const baseClasses = cn('inline-flex items-center gap-1.5 rounded-full font-medium leading-none', SIZE_CLASSES[size])

  if (variant === 'status') {
    const key = String(label).toLowerCase()
    return (
      <span className={cn(baseClasses, STATUS_COLORS[key] || 'bg-neutral-100 text-neutral-600', className)} role="status" {...props}>
        {dot && <span className={cn('h-1.5 w-1.5 rounded-full', DOT_CLASSES[key] || 'bg-neutral-400')} aria-hidden="true" />}
        {label}
      </span>
    )
  }

  if (variant === 'tier') {
    return (
      <span className={cn(baseClasses, TIER_CLASSES, className)} {...props}>
        {label}
      </span>
    )
  }

  if (variant === 'source') {
    const key = String(label).toLowerCase()
    return (
      <span className={cn(baseClasses, SOURCE_COLORS[key] || 'bg-neutral-100 text-neutral-600', className)} {...props}>
        {label}
      </span>
    )
  }

  if (variant === 'doc-status') {
    const key = String(label).toLowerCase()
    return (
      <span className={cn(baseClasses, STATUS_COLORS[key] || 'bg-neutral-100 text-neutral-600', className)} role="status" {...props}>
        {dot && <span className={cn('h-1.5 w-1.5 rounded-full', DOT_CLASSES[key] || 'bg-neutral-400')} aria-hidden="true" />}
        {label}
      </span>
    )
  }

  if (variant === 'intelligence-score') {
    const score = typeof label === 'number' ? label : Number(label)
    return (
      <span className={cn(baseClasses, getScoreColor(score), 'font-semibold tabular-nums', className)} role="status" {...props}>
        <span className="sr-only">Intelligence score: </span>
        {score}/100
      </span>
    )
  }

  if (variant === 'outline') {
    return (
      <span className={cn(baseClasses, 'border border-[var(--border-default)] text-[var(--text-muted)]', className)} {...props}>
        {label}
      </span>
    )
  }

  return (
    <span className={cn(baseClasses, 'bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]', className)} {...props}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-[var(--muhide-orange)]" aria-hidden="true" />}
      {label}
    </span>
  )
}
