'use client'

import { cn } from '@salesos/ui'
import { DollarSign, TrendingUp, AlertTriangle, Clock, Target } from 'lucide-react'
import type { PipelineViewProps } from './types'

export function PipelineView({ pipeline }: PipelineViewProps) {
  return (
    <div role="region" aria-label="ذكاء الأنابيب" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">الصفقات</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{pipeline.totalDeals}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">القيمة</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">${pipeline.totalValue >= 1e6 ? (pipeline.totalValue / 1e6).toFixed(1) + 'M' : (pipeline.totalValue / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">المرجحة</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">${pipeline.weightedValue >= 1e6 ? (pipeline.weightedValue / 1e6).toFixed(1) + 'M' : (pipeline.weightedValue / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">معدل الفوز</p>
          <p className="text-sm font-bold text-green-600">%{Math.round(pipeline.winRate * 100)}</p>
        </div>
      </div>

      {/* Stage bars */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-medium text-[var(--text-muted)]">المراحل</p>
        {pipeline.stages.map((stage) => {
          const pct = pipeline.totalValue > 0 ? (stage.value / pipeline.totalValue) * 100 : 0
          return (
            <div key={stage.id} className="flex items-center gap-2">
              <span className="w-20 text-[10px] text-[var(--text-muted)] truncate">{stage.label}</span>
              <div className="flex-1 h-5 rounded-lg bg-[var(--bg-tertiary)] overflow-hidden dark:bg-neutral-800 relative">
                <div className={cn('h-full rounded-lg transition-all', stage.color)} style={{ width: `${pct}%` }} />
              </div>
              <span className="w-16 text-right text-[10px] font-medium text-[var(--text-primary)]">{stage.deals}</span>
              <span className="w-16 text-right text-[10px] text-[var(--text-muted)]">${stage.value >= 1e6 ? (stage.value / 1e6).toFixed(1) + 'M' : (stage.value / 1e3).toFixed(0) + 'K'}</span>
            </div>
          )
        })}
      </div>

      {/* Stalled deals */}
      {pipeline.stalledDeals.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle className="h-3 w-3 text-red-500" />
            <span className="text-[10px] font-medium text-red-500">صفقات متوقفة ({pipeline.stalledDeals.length})</span>
          </div>
          {pipeline.stalledDeals.slice(0, 3).map((deal) => (
            <div key={deal.id} className="flex items-center justify-between rounded-lg bg-red-50/50 px-2 py-1.5 dark:bg-red-900/10">
              <div>
                <p className="text-[10px] text-[var(--text-primary)]">{deal.companyName} — {deal.title}</p>
                <p className="text-[9px] text-[var(--text-muted)]">متوقفة منذ {deal.daysStalled} يوم{deal.reason ? `: ${deal.reason}` : ''}</p>
              </div>
              <span className="text-[10px] font-medium text-[var(--text-primary)]">${deal.value >= 1e6 ? (deal.value / 1e6).toFixed(1) + 'M' : (deal.value / 1e3).toFixed(0) + 'K'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
