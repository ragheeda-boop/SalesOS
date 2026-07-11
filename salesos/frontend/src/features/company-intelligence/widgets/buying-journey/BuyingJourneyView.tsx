'use client'

import { cn } from '@salesos/ui'
import { TrendingUp } from 'lucide-react'
import type { BuyingJourneyViewProps } from './types'

const STAGES = ['awareness', 'interest', 'evaluation', 'decision', 'expansion'] as const
const STAGE_L: Record<string, string> = { awareness: 'وعي', interest: 'اهتمام', evaluation: 'تقييم', decision: 'قرار', expansion: 'توسع' }
const STAGE_I: Record<string, string> = { awareness: '👀', interest: '💡', evaluation: '🔍', decision: '✅', expansion: '🚀' }

export function BuyingJourneyView({ journey }: BuyingJourneyViewProps) {
  if (!journey) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <TrendingUp className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">رحلة الشراء غير متاحة</p>
      </div>
    )
  }

  const currentIdx = STAGES.indexOf(journey.currentStage)

  return (
    <div role="region" aria-label="رحلة الشراء" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Stage visual */}
      <div className="flex items-center justify-between">
        {STAGES.map((stage, i) => {
          const isActive = i === currentIdx
          const isPast = i < currentIdx
          return (
            <div key={stage} className="flex flex-col items-center">
              <div className={cn(
                'flex h-7 w-7 items-center justify-center rounded-full text-xs transition',
                isActive ? 'bg-primary-500 text-white ring-2 ring-primary-300 ring-offset-1 dark:ring-offset-neutral-900' :
                isPast ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-300' :
                'bg-[var(--bg-tertiary)] text-[var(--text-muted)] dark:bg-neutral-800',
              )}>
                {STAGE_I[stage]}
              </div>
              <span className={cn('mt-1 text-[8px]', isActive ? 'font-semibold text-primary-600 dark:text-primary-400' : 'text-[var(--text-muted)]')}>
                {STAGE_L[stage]}
              </span>
            </div>
          )
        })}
      </div>

      {/* Progress */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] dark:bg-neutral-700">
        <div className="h-full rounded-full bg-primary-500 transition-all" style={{ width: `${journey.progress}%` }} />
      </div>
      <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
        <span>%{journey.progress} مكتمل</span>
        <span>{journey.timeInStage} في المرحلة</span>
      </div>

      {/* Stage description */}
      <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
        <p className="text-[10px] text-[var(--text-muted)]">{journey.stageDescription}</p>
      </div>

      {/* Recommended action */}
      <div className="flex items-center gap-2 rounded-lg bg-primary-50 p-2 dark:bg-primary-900/10">
        <TrendingUp className="h-4 w-4 shrink-0 text-primary-600" />
        <div>
          <p className="text-[10px] font-medium text-primary-700 dark:text-primary-300">الإجراء الموصى به</p>
          <p className="text-xs text-primary-800 dark:text-primary-200">{journey.recommendedAction}</p>
        </div>
      </div>
    </div>
  )
}
