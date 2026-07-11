'use client'

import { useMemo } from 'react'
import { cn } from '@salesos/ui'
import { Activity, Calendar, Mail, CheckCircle2, DollarSign, FileText } from 'lucide-react'
import type { RevenueTimelineViewProps } from './types'

const TYPE_CFG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  signal: { icon: <Activity className="h-3 w-3" />, label: 'إشارة', color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20' },
  meeting: { icon: <Calendar className="h-3 w-3" />, label: 'اجتماع', color: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20' },
  email: { icon: <Mail className="h-3 w-3" />, label: 'بريد', color: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20' },
  task: { icon: <CheckCircle2 className="h-3 w-3" />, label: 'مهمة', color: 'text-green-600 bg-green-50 dark:bg-green-900/20' },
  deal: { icon: <DollarSign className="h-3 w-3" />, label: 'صفقة', color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20' },
  note: { icon: <FileText className="h-3 w-3" />, label: 'ملاحظة', color: 'text-neutral-600 bg-neutral-50 dark:bg-neutral-800' },
}

export function RevenueTimelineView({ events }: RevenueTimelineViewProps) {
  const sorted = useMemo(() => [...events].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()), [events])

  if (sorted.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Activity className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد أحداث</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="الجدول الزمني للإيرادات" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {sorted.slice(0, 25).map((evt) => {
        const cfg = TYPE_CFG[evt.type] ?? TYPE_CFG.note
        return (
          <div key={evt.id} className="flex items-start gap-3 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
            <div className={cn('flex h-6 w-6 shrink-0 items-center justify-center rounded-full', cfg.color)}>
              {cfg.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className={cn('rounded px-1 py-0.5 text-[9px] font-medium', cfg.color)}>{cfg.label}</span>
                {evt.entityName && <span className="text-[9px] text-[var(--text-muted)]">{evt.entityName}</span>}
              </div>
              <p className="text-[10px] text-[var(--text-primary)]">{evt.summary}</p>
              <div className="flex items-center gap-2 text-[8px] text-[var(--text-muted)]">
                <span>{new Date(evt.date).toLocaleDateString('ar-SA')}</span>
                {evt.value && <span>${evt.value >= 1e6 ? (evt.value / 1e6).toFixed(1) + 'M' : (evt.value / 1e3).toFixed(0) + 'K'}</span>}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
