'use client'

import { cn } from '@salesos/ui'
import { AlertTriangle, DollarSign, Clock, TrendingDown } from 'lucide-react'
import type { ChurnData } from './types'

export function ChurnView({ data }: { data: ChurnData }) {
  return (
    <div role="region" aria-label="مخاطر التوقف" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-red-50 p-2 dark:bg-red-900/10">
          <p className="text-[9px] text-red-600">في خطر</p>
          <p className="text-sm font-bold text-red-700">{data.totalAtRisk}</p>
        </div>
        <div className="rounded-lg bg-red-50 p-2 dark:bg-red-900/10">
          <p className="text-[9px] text-red-600">الإيرادات</p>
          <p className="text-sm font-bold text-red-700">${data.totalRevenue >= 1e6 ? (data.totalRevenue / 1e6).toFixed(1) + 'M' : (data.totalRevenue / 1e3).toFixed(0) + 'K'}</p>
        </div>
        <div className="rounded-lg bg-red-50 p-2 dark:bg-red-900/10">
          <p className="text-[9px] text-red-600">معدل الخطر</p>
          <p className="text-sm font-bold text-red-700">%{Math.round(data.avgRiskScore * 100)}</p>
        </div>
      </div>
      {data.atRiskAccounts.map((a, i) => (
        <div key={i} className="flex items-start gap-2 rounded-lg px-2 py-1.5 transition hover:bg-[var(--bg-tertiary)]">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium text-[var(--text-primary)]">{a.companyName}</span>
              <span className={cn('mr-auto rounded px-1 py-0.5 text-[8px] font-medium', a.riskScore >= 0.7 ? 'bg-red-100 text-red-700 dark:bg-red-900/30' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30')}>
                %{Math.round(a.riskScore * 100)}
              </span>
            </div>
            <p className="text-[9px] text-[var(--text-muted)]">{a.reason}</p>
            <div className="flex items-center gap-2 text-[8px] text-[var(--text-muted)]">
              <Clock className="h-2.5 w-2.5" /> {a.daysSinceActivity} يوم بدون نشاط
              <span>·</span>
              <span>${a.revenue >= 1e6 ? (a.revenue / 1e6).toFixed(1) + 'M' : (a.revenue / 1e3).toFixed(0) + 'K'}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
