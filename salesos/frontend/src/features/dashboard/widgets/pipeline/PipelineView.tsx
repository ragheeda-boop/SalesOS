'use client'

import { useCallback, useMemo } from 'react'
import { cn } from '@salesos/ui'
import type { PipelineViewProps, PipelineDeal, PipelineStage } from './types'

const VIRTUALIZE_THRESHOLD = 50

function StageBar({ stage, maxValue }: { stage: PipelineStage; maxValue: number }) {
  const widthPercent = maxValue > 0 ? (stage.value / maxValue) * 100 : 0

  return (
    <div
      className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none"
      aria-label={`${stage.name}: ${stage.count} صفقة بقيمة ${stage.value.toLocaleString()} ريال`}
    >
      <div className="min-w-[80px]">
        <div className="font-medium text-[var(--text-primary)]">{stage.name}</div>
        <div className="text-[10px] text-[var(--text-muted)]">{stage.count} صفقة</div>
      </div>
      <div className="flex-1">
        <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
          <div
            className="h-full rounded-full transition-all duration-300 motion-reduce:transition-none"
            style={{ width: `${widthPercent}%`, backgroundColor: stage.color }}
            role="progressbar"
            aria-valuenow={Math.round(widthPercent)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${stage.name} progress`}
          />
        </div>
      </div>
      <span className="shrink-0 text-xs font-medium text-[var(--text-secondary)]">
        {stage.value >= 1_000_000
          ? `${(stage.value / 1_000_000).toFixed(1)}M`
          : stage.value >= 1_000
            ? `${(stage.value / 1_000).toFixed(0)}K`
            : stage.value}
      </span>
    </div>
  )
}

function DealRow({ deal, onClick }: { deal: PipelineDeal; onClick?: (id: string) => void }) {
  const handleClick = useCallback(() => onClick?.(deal.id), [deal.id, onClick])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onClick(deal.id)
    }
  }, [deal.id, onClick])

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        onClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)] focus-visible:ring-offset-1',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${deal.title} - ${deal.companyName} - ${deal.stage} - ${deal.probability}% احتمال`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium text-[var(--text-primary)]">{deal.title}</span>
          <span className="shrink-0 rounded-full bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
            {deal.stage}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <span>{deal.companyName}</span>
          <span>· احتمال {deal.probability}%</span>
          {deal.daysInStage > 0 && <span>· {deal.daysInStage} يوم</span>}
        </div>
      </div>
      <span className="shrink-0 text-xs font-medium text-[var(--text-secondary)]">
        {deal.value.toLocaleString('ar-SA')} ريال
      </span>
    </div>
  )
}

function SkeletonStages() {
  return (
    <div className="space-y-2" role="status" aria-label="جاري تحميل الأنبوب">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center gap-3 rounded-lg px-3 py-2">
          <div className="h-3 w-16 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
          <div className="flex-1 h-2 animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-700" />
          <div className="h-3 w-8 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
        </div>
      ))}
    </div>
  )
}

function VirtualizedDealList({ deals, onDealClick }: { deals: PipelineDeal[]; onDealClick?: (id: string) => void }) {
  const visibleDeals = useMemo(() => deals.slice(0, VIRTUALIZE_THRESHOLD), [deals])
  const remaining = deals.length - VIRTUALIZE_THRESHOLD

  return (
    <div>
      <div role="list" aria-label="صفقات الأنبوب" className="space-y-1">
        {visibleDeals.map((deal) => (
          <div key={deal.id} role="listitem">
            <DealRow deal={deal} onClick={onDealClick} />
          </div>
        ))}
      </div>
      {remaining > 0 && (
        <div className="mt-1 px-3 text-[10px] text-[var(--text-muted)]">
          +{remaining} صفقة أخرى
        </div>
      )}
    </div>
  )
}

function DealList({ deals, onDealClick }: { deals: PipelineDeal[]; onDealClick?: (id: string) => void }) {
  if (deals.length > VIRTUALIZE_THRESHOLD) {
    return <VirtualizedDealList deals={deals} onDealClick={onDealClick} />
  }

  return (
    <div role="list" aria-label="صفقات الأنبوب" className="space-y-1">
      {deals.map((deal) => (
        <div key={deal.id} role="listitem">
          <DealRow deal={deal} onClick={onDealClick} />
        </div>
      ))}
    </div>
  )
}

export function PipelineView({
  stages,
  deals,
  totalValue,
  dealCount,
  decision,
  nbaItems,
  isDecisionLoading,
  onDealClick,
}: PipelineViewProps) {
  const maxValue = useMemo(() => Math.max(...stages.map((s) => s.value), 1), [stages])

  if (isDecisionLoading && stages.length === 0) {
    return <SkeletonStages />
  }

  if (stages.length === 0 && deals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">📊</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">لا توجد بيانات الأنبوب</p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">ستظهر صفقاتك هنا عند إضافتها</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="أنابيب المبيعات" className="space-y-4">
      {decision && (
        <div
          aria-live="polite"
          aria-atomic="true"
          className="rounded-lg bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-muted)]"
        >
          <span className="font-medium text-[var(--text-primary)]">ملخص الأنبوب: </span>
          {decision.summary}
          <span className="ml-1 text-[10px] opacity-60">
            ({Math.round(decision.confidence * 100)}% ثقة)
          </span>
        </div>
      )}

      <div>
        <div className="mb-1 flex items-center justify-between px-1">
          <span className="text-xs font-semibold text-[var(--text-muted)]">مراحل الأنبوب</span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {dealCount} صفقة — {(totalValue / 1_000_000).toFixed(1)}M ريال
          </span>
        </div>
        <div
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          إجمالي الأنبوب: {dealCount} صفقة بقيمة {totalValue.toLocaleString('ar-SA')} ريال
        </div>
        <div className="space-y-0.5">
          {stages.map((stage) => (
            <StageBar key={stage.id} stage={stage} maxValue={maxValue} />
          ))}
        </div>
      </div>

      {deals.length > 0 && (
        <div>
          <div className="mb-1 px-1 text-xs font-semibold text-[var(--text-muted)]">الصفقات النشطة</div>
          <DealList deals={deals} onDealClick={onDealClick} />
        </div>
      )}

      {nbaItems && nbaItems.length > 0 && (
        <div className="border-t border-[var(--border-secondary)] pt-2">
          <div className="mb-1 text-[10px] font-semibold text-[var(--text-muted)]">توصيات AI للأنبوب</div>
          {nbaItems.slice(0, 2).map((nba) => (
            <div
              key={nba.id}
              className="rounded-md px-2 py-1 text-xs text-[var(--text-muted)]"
              aria-label={`AI توصية: ${nba.action} لـ ${nba.company_name}`}
            >
              <span className="font-medium text-[var(--text-primary)]">{nba.company_name}</span>
              {' — '}
              {nba.action}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
