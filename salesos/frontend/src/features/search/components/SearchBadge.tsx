'use client'

import { cn } from '@salesos/ui'

interface SearchBadgeProps {
  label: string
  variant?: 'info' | 'success' | 'warning' | 'danger' | 'neutral'
  className?: string
}

const VARIANT_STYLE: Record<string, string> = {
  info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  success: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  danger: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  neutral: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
}

export function SearchBadge({ label, variant = 'neutral', className }: SearchBadgeProps) {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium', VARIANT_STYLE[variant], className)}>
      {label}
    </span>
  )
}
