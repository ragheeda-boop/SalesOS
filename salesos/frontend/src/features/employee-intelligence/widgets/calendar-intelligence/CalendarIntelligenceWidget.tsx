'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { CalendarIntelligence } from '@/lib/api'
import { Calendar, Clock, Building2, ChevronLeft } from 'lucide-react'

export function CalendarIntelligenceView({ data }: { data: CalendarIntelligence }) {
  const formatTime = (ts: string) => {
    const d = new Date(ts)
    return d.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (ts: string) => {
    const d = new Date(ts)
    const now = new Date()
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (d.toDateString() === now.toDateString()) return 'اليوم'
    if (d.toDateString() === tomorrow.toDateString()) return 'غداً'
    return d.toLocaleDateString('ar-SA', { weekday: 'short', day: 'numeric', month: 'short' })
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-[var(--bg-secondary)] p-2.5 text-center">
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.today_count}</p>
          <p className="text-[9px] text-[var(--text-muted)]">اليوم</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-2.5 text-center">
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.week_count}</p>
          <p className="text-[9px] text-[var(--text-muted)]">هذا الأسبوع</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-2.5 text-center">
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.month_count}</p>
          <p className="text-[9px] text-[var(--text-muted)]">هذا الشهر</p>
        </div>
      </div>

      <div className="space-y-1.5 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[var(--text-muted)] flex items-center gap-1">
            <Clock className="h-3 w-3" /> إجمالي الساعات
          </span>
          <span className="text-[var(--text-secondary)] font-medium">{data.total_hours.toFixed(1)} ساعة</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[var(--text-muted)] flex items-center gap-1">
            <Building2 className="h-3 w-3" /> شركات تم لقاؤها
          </span>
          <span className="text-[var(--text-secondary)] font-medium">{data.unique_companies_met}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[var(--text-muted)] flex items-center gap-1">
            <Clock className="h-3 w-3" /> متوسط المدة
          </span>
          <span className="text-[var(--text-secondary)] font-medium">{Math.round(data.avg_duration_minutes)} دقيقة</span>
        </div>
      </div>

      {data.upcoming.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">الاجتماعات القادمة</p>
          <div className="space-y-1.5 max-h-28 overflow-y-auto">
            {data.upcoming.slice(0, 5).map((meeting: Record<string, unknown>, i: number) => (
              <div key={(meeting.id as string) || i} className="flex items-center gap-2 text-xs py-1.5 px-2 rounded-lg hover:bg-[var(--bg-secondary)]">
                <Calendar className="h-3 w-3 text-[var(--muhide-orange)] shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[var(--text-secondary)]">{(meeting.title as string) || (meeting.summary as string) || 'اجتماع'}</p>
                  <p className="text-[9px] text-[var(--text-muted)]">
                    {formatDate((meeting.start_time as string) || (meeting.date as string) || '')}
                    {meeting.start_time ? ` · ${formatTime(meeting.start_time as string)}` : ''}
                  </p>
                </div>
                <ChevronLeft className="h-3 w-3 text-[var(--text-muted)] shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}

      {!data.upcoming.length && data.today_count === 0 && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <Calendar className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-1" />
          <p className="text-xs text-[var(--text-muted)]">لا توجد اجتماعات مجدولة</p>
        </div>
      )}
    </div>
  )
}

export const CalendarIntelligenceWidget = createWorkspaceWidget(
  { id: 'calendarIntelligence', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.calendar,
  {
    metadata: { title: 'ذكاء التقويم' },
    render: ({ data }) => <CalendarIntelligenceView data={data} />,
  },
)
