'use client'

import { cn } from '@salesos/ui'
import { TrendingUp, DollarSign, Target, AlertTriangle } from 'lucide-react'
import type { ForecastData } from './types'

export function ForecastView({ data }: { data: ForecastData }) {
  const progress = data.currentQuarter.target > 0 ? (data.currentQuarter.actual / data.currentQuarter.target) * 100 : 0
  const projectedPct = data.currentQuarter.target > 0 ? (data.currentQuarter.projected / data.currentQuarter.target) * 100 : 0

  return (
    <div role="region" aria-label="التوقعات" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">الهدف</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">${data.currentQuarter.target >= 1e6 ? (data.currentQuarter.target / 1e6).toFixed(1) + 'M' : (data.currentQuarter.target / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">الفعلي</p>
          <p className="text-sm font-bold text-green-600">${data.currentQuarter.actual >= 1e6 ? (data.currentQuarter.actual / 1e6).toFixed(1) + 'M' : (data.currentQuarter.actual / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">المتوقع</p>
          <p className="text-sm font-bold text-amber-600">${data.currentQuarter.projected >= 1e6 ? (data.currentQuarter.projected / 1e6).toFixed(1) + 'M' : (data.currentQuarter.projected / 1e3).toFixed(0) + 'K'}</p>
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)]"><span>التقدم</span><span>%{Math.round(progress)}</span></div>
        <div className="mt-1 h-3 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] dark:bg-neutral-700">
          <div className="h-full rounded-full bg-green-500 transition-all" style={{ width: `${Math.min(progress, 100)}%` }} />
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between text-xs text-[var(--text-muted)]"><span>المتوقع</span><span>%{Math.round(projectedPct)} من الهدف</span></div>
        <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] dark:bg-neutral-700">
          <div className={cn('h-full rounded-full transition-all', projectedPct >= 100 ? 'bg-green-500' : projectedPct >= 80 ? 'bg-amber-500' : 'bg-red-500')} style={{ width: `${Math.min(projectedPct, 100)}%` }} />
        </div>
      </div>
      {data.risks.length > 0 && (
        <div>
          <p className="mb-1 flex items-center gap-1 text-[10px] font-medium text-red-500"><AlertTriangle className="h-3 w-3" /> المخاطر</p>
          {data.risks.map((r, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg bg-red-50/50 px-2 py-1 dark:bg-red-900/10">
              <span className="text-[10px] text-[var(--text-primary)]">{r.label}</span>
              <span className="text-[9px] text-red-500">%{Math.round(r.probability * 100)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
