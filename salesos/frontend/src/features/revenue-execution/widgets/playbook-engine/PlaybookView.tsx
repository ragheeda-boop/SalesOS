'use client'

import { cn } from '@salesos/ui'
import { BookOpen, CheckCircle, Clock, TrendingUp } from 'lucide-react'
import type { PlaybookViewProps } from './types'

export function PlaybookView({ playbook, industry }: PlaybookViewProps) {
  return (
    <div role="region" aria-label="محرك اللعب" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {playbook ? (
        <>
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary-600" />
            <span className="text-xs font-bold text-[var(--text-primary)]">{playbook.name}</span>
            <span className="mr-auto rounded-full bg-green-50 px-1.5 py-0.5 text-[9px] font-medium text-green-600 dark:bg-green-900/20 dark:text-green-300">
              %{playbook.successRate} نجاح
            </span>
          </div>
          <p className="text-[10px] text-[var(--text-muted)]">{playbook.description}</p>
          <div className="flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
            <Clock className="h-3 w-3" /> {playbook.estimatedDuration}
            <span>·</span>
            <span>{playbook.steps.length} خطوات</span>
          </div>
          <div className="space-y-1">
            {playbook.steps.map((step) => (
              <div key={step.id} className="flex items-start gap-2 rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-100 text-[9px] font-bold text-primary-600 dark:bg-primary-900/30 dark:text-primary-300">
                  {step.order}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-medium text-[var(--text-primary)]">{step.title}</p>
                  <p className="text-[9px] text-[var(--text-muted)]">{step.description}</p>
                  <p className="text-[8px] text-[var(--text-muted)]">{step.duration}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <BookOpen className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
          <p className="text-sm text-[var(--text-muted)]">لا يوجد دليل لعب متاح</p>
          <p className="text-xs text-[var(--text-muted)]">للقطاع: {industry}</p>
        </div>
      )}
    </div>
  )
}
