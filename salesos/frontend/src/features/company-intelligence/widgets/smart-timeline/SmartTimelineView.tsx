'use client'

import { useMemo } from 'react'
import { cn } from '@salesos/ui'
import { Activity, Newspaper, Shield, Mail, Calendar, FileText, Award, Briefcase, DollarSign, Sparkles } from 'lucide-react'
import type { SmartTimelineViewProps } from './types'

const TYPE_CFG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  signal: { icon: <Activity className="h-3 w-3" />, label: 'إشارة', color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-300' },
  news: { icon: <Newspaper className="h-3 w-3" />, label: 'خبر', color: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-300' },
  government: { icon: <Shield className="h-3 w-3" />, label: 'حكومي', color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-300' },
  email: { icon: <Mail className="h-3 w-3" />, label: 'بريد', color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-300' },
  meeting: { icon: <Calendar className="h-3 w-3" />, label: 'اجتماع', color: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-300' },
  crm: { icon: <Award className="h-3 w-3" />, label: 'CRM', color: 'text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20 dark:text-cyan-300' },
  document: { icon: <FileText className="h-3 w-3" />, label: 'مستند', color: 'text-slate-600 bg-slate-50 dark:bg-slate-900/20 dark:text-slate-300' },
  license: { icon: <Shield className="h-3 w-3" />, label: 'رخصة', color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-300' },
  hiring: { icon: <Briefcase className="h-3 w-3" />, label: 'توظيف', color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 dark:text-indigo-300' },
  funding: { icon: <DollarSign className="h-3 w-3" />, label: 'تمويل', color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-300' },
  ai: { icon: <Sparkles className="h-3 w-3" />, label: 'AI', color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-300' },
}

export function SmartTimelineView({ events }: SmartTimelineViewProps) {
  const sorted = useMemo(() =>
    [...events].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
  [events])

  if (sorted.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Activity className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد أحداث في الجدول الزمني</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="الجدول الزمني الذكي" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {sorted.slice(0, 20).map((evt) => {
        const cfg = TYPE_CFG[evt.type] ?? TYPE_CFG.signal
        return (
          <div key={evt.id} className={cn('flex items-start gap-3 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]', evt.aiHighlighted && 'bg-purple-50/30 dark:bg-purple-900/5')}>
            <div className={cn('flex h-6 w-6 shrink-0 items-center justify-center rounded-full', cfg.color)}>
              {cfg.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className={cn('rounded px-1 py-0.5 text-[9px] font-medium', cfg.color)}>{cfg.label}</span>
                {evt.aiHighlighted && <Sparkles className="h-3 w-3 text-purple-500" />}
              </div>
              <p className="mt-0.5 text-xs text-[var(--text-primary)]">{evt.summary}</p>
              <div className="mt-0.5 flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
                <span>{new Date(evt.date).toLocaleDateString('ar-SA')}</span>
                <span>{evt.source}</span>
                {evt.confidence && <span>%{Math.round(evt.confidence * 100)}</span>}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
