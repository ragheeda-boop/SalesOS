'use client'

import type { MissionProgressProps } from './types'

export function MissionProgress({ value, max, label, barClassName }: MissionProgressProps) {
  const pct = max > 0 ? Math.min(Math.round((value / max) * 100), 100) : 0

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label}
      aria-valuetext={`${pct}%`}
      className="flex flex-col gap-1"
    >
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-[var(--text-primary)]">{label}</span>
        <span className="text-[var(--text-muted)]" aria-hidden="true">{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-700" aria-hidden="true">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            'motion-reduce:transition-none motion-reduce:duration-0',
            barClassName ?? 'bg-[var(--muhide-orange)]',
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

import { cn } from '@salesos/ui'
