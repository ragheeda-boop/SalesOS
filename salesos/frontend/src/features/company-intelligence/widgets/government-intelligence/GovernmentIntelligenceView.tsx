'use client'

import { cn } from '@salesos/ui'
import { Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import type { GovernmentIntelligenceViewProps } from './types'

const STATUS_V = { active: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300', expired: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300', pending: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300', violation: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300' }
const STATUS_L = { active: 'ساري', expired: 'منتهي', pending: 'قيد الانتظار', violation: 'مخالفة' }

export function GovernmentIntelligenceView({ records }: GovernmentIntelligenceViewProps) {
  if (records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Shield className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد سجلات حكومية</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="البيانات الحكومية" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {records.map((r) => (
        <div key={r.id} className="flex items-start gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <div className="mt-0.5">
            {r.status === 'violation' || r.status === 'expired'
              ? <AlertTriangle className="h-4 w-4 text-red-500" />
              : r.status === 'pending'
              ? <Clock className="h-4 w-4 text-amber-500" />
              : <CheckCircle className="h-4 w-4 text-green-500" />
            }
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-[var(--text-primary)]">{r.title}</span>
              <span className={cn('mr-auto rounded px-1 py-0.5 text-[9px] font-medium', STATUS_V[r.status] ?? STATUS_V.active)}>
                {STATUS_L[r.status] ?? r.status}
              </span>
            </div>
            <div className="mt-0.5 flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
              <span>{r.source}</span>
              {r.expiryDate && <span>ينتهي: {new Date(r.expiryDate).toLocaleDateString('ar-SA')}</span>}
              <span>%{Math.round(r.confidence * 100)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
