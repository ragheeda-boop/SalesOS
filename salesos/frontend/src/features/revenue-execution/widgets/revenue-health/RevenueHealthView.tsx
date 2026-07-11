'use client'

import { cn } from '@salesos/ui'
import { Activity, TrendingUp, AlertTriangle, Users } from 'lucide-react'
import type { RevenueHealthData } from './types'

export function RevenueHealthView({ data }: { data: RevenueHealthData }) {
  return (
    <div role="region" aria-label="صحة الإيرادات" className="space-y-3 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-4 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]">الحسابات</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.totalPortfolio}</p>
        </div>
        <div className="rounded-lg bg-green-50 p-2 dark:bg-green-900/10">
          <p className="text-[9px] text-green-600">نشطة</p>
          <p className="text-sm font-bold text-green-700">{data.activeAccounts}</p>
        </div>
        <div className="rounded-lg bg-red-50 p-2 dark:bg-red-900/10">
          <p className="text-[9px] text-red-600">في خطر</p>
          <p className="text-sm font-bold text-red-700">{data.atRisk}</p>
        </div>
        <div className="rounded-lg bg-green-50 p-2 dark:bg-green-900/10">
          <p className="text-[9px] text-green-600">نمو</p>
          <p className="text-sm font-bold text-green-700">{data.growthAccounts}</p>
        </div>
      </div>
      <div className="space-y-1.5">
        {data.healthDistribution.map((h) => (
          <div key={h.label} className="flex items-center gap-2">
            <span className="w-16 text-[10px] text-[var(--text-muted)] truncate">{h.label}</span>
            <div className="flex-1 h-4 rounded-lg bg-[var(--bg-tertiary)] overflow-hidden dark:bg-neutral-800">
              <div className={cn('h-full rounded-lg transition-all', h.color)} style={{ width: `${(h.value / data.activeAccounts / 100) * 100}%` }} />
            </div>
            <span className="w-8 text-right text-[10px] text-[var(--text-muted)]">{h.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
