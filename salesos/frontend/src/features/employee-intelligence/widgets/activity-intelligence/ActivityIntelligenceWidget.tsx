'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { ActivityIntelligence } from '@/lib/api'
import { Calendar, Mail, Phone, CheckSquare, FileText, MessageSquare, Activity } from 'lucide-react'
import { cn } from '@salesos/ui'

const activityIcons: Record<string, React.ReactNode> = {
  meetings: <Calendar className="h-3.5 w-3.5" />,
  emails: <Mail className="h-3.5 w-3.5" />,
  calls: <Phone className="h-3.5 w-3.5" />,
  tasks: <CheckSquare className="h-3.5 w-3.5" />,
  notes: <FileText className="h-3.5 w-3.5" />,
  documents: <FileText className="h-3.5 w-3.5" />,
}

const activityColors: Record<string, string> = {
  meetings: 'text-blue-600 bg-blue-50',
  emails: 'text-amber-600 bg-amber-50',
  calls: 'text-green-600 bg-green-50',
  tasks: 'text-purple-600 bg-purple-50',
  notes: 'text-cyan-600 bg-cyan-50',
  documents: 'text-rose-600 bg-rose-50',
}

export function ActivityIntelligenceView({ data }: { data: ActivityIntelligence }) {
  const activityItems = [
    { key: 'meetings', label: 'اجتماعات', value: data.meetings },
    { key: 'emails', label: 'بريد', value: data.emails },
    { key: 'calls', label: 'مكالمات', value: data.calls },
    { key: 'tasks', label: 'مهام', value: data.tasks },
  ]

  const formatTime = (ts: string) => {
    const d = new Date(ts)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const hours = Math.floor(diff / 3600000)
    if (hours < 1) return 'الآن'
    if (hours < 24) return `منذ ${hours} ساعة`
    return d.toLocaleDateString('ar-SA')
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-4 gap-2">
        {activityItems.map((item) => (
          <div key={item.key} className="rounded-lg p-2 text-center bg-[var(--bg-secondary)]">
            <div className={cn('flex items-center justify-center w-7 h-7 rounded-lg mx-auto mb-1', activityColors[item.key])}>
              {activityIcons[item.key]}
            </div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">{item.value}</p>
            <p className="text-[9px] text-[var(--text-muted)]">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--text-secondary)] font-medium">إجمالي النشاطات</span>
        <span className="text-lg font-semibold text-[var(--text-primary)]">{data.total}</span>
      </div>

      {data.recent.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">آخر النشاطات</p>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {data.recent.slice(0, 10).map((item: Record<string, string | undefined>, i: number) => (
              <div key={item.id || i} className="flex items-start gap-2 text-xs py-1">
                <Activity className="h-3 w-3 text-[var(--text-muted)] mt-0.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[var(--text-secondary)]">{item.description || item.action || 'نشاط'}</p>
                  <p className="text-[9px] text-[var(--text-muted)]">{item.timestamp ? formatTime(item.timestamp) : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!data.recent.length && data.total === 0 && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <MessageSquare className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-1" />
          <p className="text-xs text-[var(--text-muted)]">لا توجد نشاطات حديثة</p>
        </div>
      )}
    </div>
  )
}

export const ActivityIntelligenceWidget = createWorkspaceWidget(
  { id: 'activityIntelligence', minHeight: '340px' },
  useWorkspaceContext,
  (widgets) => widgets.activity,
  {
    metadata: { title: 'ذكاء النشاطات' },
    render: ({ data }) => <ActivityIntelligenceView data={data} />,
  },
)
