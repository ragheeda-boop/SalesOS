'use client'

import { cn } from '@salesos/ui'
import { User, Star, Mail, Phone } from 'lucide-react'
import type { DecisionMakersViewProps } from './types'

const INF_C = { high: 'text-green-600 dark:text-green-400', medium: 'text-amber-600 dark:text-amber-400', low: 'text-neutral-400' }
const INF_L = { high: 'عالي', medium: 'متوسط', low: 'منخفض' }

export function DecisionMakersView({ makers }: DecisionMakersViewProps) {
  if (makers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <User className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد جهات اتصال</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="صناع القرار" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {makers.map((m) => (
        <div key={m.id} className="flex items-start gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-300">
            <User className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="truncate text-sm font-medium text-[var(--text-primary)]">{m.name}</span>
              {m.connected && <Star className="h-3 w-3 shrink-0 fill-amber-400 text-amber-400" />}
              <span className={cn('mr-auto text-[10px] font-medium', INF_C[m.influence])}>{INF_L[m.influence]}</span>
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">{m.role} · {m.department}</p>
            {m.lastInteraction && (
              <p className="text-[10px] text-[var(--text-muted)]">آخر تواصل: {m.lastInteraction}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
