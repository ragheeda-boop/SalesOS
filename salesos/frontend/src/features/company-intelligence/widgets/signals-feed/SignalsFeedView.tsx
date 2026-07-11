'use client'

import { cn } from '@salesos/ui'
import { Activity, Sparkles } from 'lucide-react'
import type { SignalsFeedViewProps } from './types'

const SEV_C = { low: 'text-neutral-500 bg-neutral-50 dark:bg-neutral-800 dark:text-neutral-400', medium: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-300', high: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-300', critical: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-300' }
const SEV_L = { low: 'منخفض', medium: 'متوسط', high: 'عالي', critical: 'حرج' }

export function SignalsFeedView({ signals }: SignalsFeedViewProps) {
  if (signals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Activity className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد إشارات</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="الإشارات" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {signals.map((s) => (
        <div key={s.id} className="flex items-start gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <Activity className="mt-1 h-4 w-4 shrink-0 text-[var(--text-muted)]" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="truncate text-xs font-medium text-[var(--text-primary)]">{s.title}</span>
              <span className={cn('mr-auto rounded px-1 py-0.5 text-[9px] font-medium', SEV_C[s.severity])}>{SEV_L[s.severity]}</span>
            </div>
            <p className="mt-0.5 text-[10px] text-[var(--text-muted)] line-clamp-1">{s.description}</p>
            <div className="flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
              <span>{s.source}</span>
              {s.aiConfidence > 0 && (
                <span className="flex items-center gap-0.5 text-purple-500">
                  <Sparkles className="h-2.5 w-2.5" />%{Math.round(s.aiConfidence * 100)}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
