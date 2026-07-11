'use client'

import { cn } from '@salesos/ui'
import { TrendingUp, DollarSign } from 'lucide-react'
import type { ExpansionData } from './types'

export function ExpansionView({ data }: { data: ExpansionData }) {
  return (
    <div role="region" aria-label="فرص التوسع" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">قيمة الفرص</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">${data.totalValue >= 1e6 ? (data.totalValue / 1e6).toFixed(1) + 'M' : (data.totalValue / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">متوسط الثقة</p>
          <p className="text-sm font-bold text-green-600">%{Math.round(data.avgConfidence * 100)}</p>
        </div>
      </div>
      {data.opportunities.map((o, i) => (
        <div key={i} className="flex items-start gap-2 rounded-lg px-2 py-1.5 transition hover:bg-[var(--bg-tertiary)]">
          <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium text-[var(--text-primary)]">{o.companyName}</span>
              <span className="text-[9px] text-[var(--text-muted)]">{o.product}</span>
            </div>
            <p className="text-[9px] text-[var(--text-muted)]">{o.reason}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-medium text-[var(--text-primary)]">${o.value >= 1e6 ? (o.value / 1e6).toFixed(1) + 'M' : (o.value / 1e3).toFixed(0) + 'K'}</p>
            <p className="text-[8px] text-[var(--text-muted)]">%{Math.round(o.confidence * 100)}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
