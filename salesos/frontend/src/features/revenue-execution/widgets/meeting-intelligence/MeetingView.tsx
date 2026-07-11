'use client'

import { cn } from '@salesos/ui'
import { Calendar, Users, Activity, AlertTriangle, TrendingUp, MessageSquare, Target } from 'lucide-react'
import type { MeetingViewProps } from './types'

export function MeetingView({ brief }: MeetingViewProps) {
  if (!brief) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Calendar className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا يوجد إيجاز اجتماع</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="ذكاء الاجتماعات" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-primary-600" />
        <div>
          <p className="text-xs font-bold text-[var(--text-primary)]">{brief.meetingTitle}</p>
          <p className="text-[9px] text-[var(--text-muted)]">{brief.companyName} · {new Date(brief.date).toLocaleDateString('ar-SA')}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="flex items-center gap-1 text-[9px] text-[var(--text-muted)]"><Users className="h-3 w-3" /> الحضور</p>
          {brief.attendees.map((a, i) => (
            <p key={i} className="text-[10px] text-[var(--text-primary)]">{a.name} <span className="text-[var(--text-muted)]">({a.role})</span></p>
          ))}
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="flex items-center gap-1 text-[9px] text-[var(--text-muted)]"><Activity className="h-3 w-3" /> الإشارات</p>
          {brief.recentSignals.map((s, i) => (
            <p key={i} className="text-[10px] text-purple-600 dark:text-purple-400">• {s}</p>
          ))}
        </div>
      </div>

      {brief.risks.length > 0 && (
        <div className="rounded-lg bg-red-50/50 p-2 dark:bg-red-900/10">
          <p className="flex items-center gap-1 text-[9px] font-medium text-red-500"><AlertTriangle className="h-3 w-3" /> المخاطر</p>
          {brief.risks.map((r, i) => <p key={i} className="text-[10px] text-red-600 dark:text-red-400">• {r}</p>)}
        </div>
      )}

      <div className="space-y-1">
        <p className="flex items-center gap-1 text-[9px] font-medium text-[var(--text-muted)]"><MessageSquare className="h-3 w-3" /> نقاط النقاش</p>
        {brief.talkingPoints.map((tp, i) => (
          <div key={i} className="rounded-lg bg-[var(--bg-tertiary)] px-2 py-1 dark:bg-neutral-800">
            <p className="text-[10px] text-[var(--text-primary)]">{tp}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 rounded-lg bg-primary-50 p-2 dark:bg-primary-900/10">
        <Target className="h-4 w-4 text-primary-600" />
        <p className="text-[10px] font-medium text-primary-700 dark:text-primary-300">{brief.recommendedAction}</p>
      </div>
    </div>
  )
}
