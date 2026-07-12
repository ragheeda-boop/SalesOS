'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { EmailIntelligence } from '@/lib/api'
import { Mail, Send, Inbox, Reply, Clock, Users } from 'lucide-react'

export function EmailIntelligenceView({ data }: { data: EmailIntelligence }) {
  const responseTimeText = data.avg_response_hours > 0
    ? data.avg_response_hours < 1
      ? 'أقل من ساعة'
      : `${Math.round(data.avg_response_hours)} ساعة`
    : '—'

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Send className="h-3 w-3" /> مرسل
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.sent}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Inbox className="h-3 w-3" /> مستلم
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.received}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Reply className="h-3 w-3" /> ردود
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{data.replies}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Clock className="h-3 w-3" /> وقت الرد
          </div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">{responseTimeText}</p>
        </div>
      </div>

      {data.top_contacts.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2 flex items-center gap-1">
            <Users className="h-3 w-3" /> أهم جهات الاتصال
          </p>
          <div className="space-y-1.5">
            {data.top_contacts.slice(0, 4).map((contact: Record<string, string | number | undefined>, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs py-1">
                <Mail className="h-3 w-3 text-[var(--text-muted)] shrink-0" />
                <span className="text-[var(--text-secondary)]">{contact.name || contact.email || 'جهة اتصال'}</span>
                {contact.count && (
                  <span className="mr-auto text-[var(--text-muted)]">{contact.count} رسالة</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.top_companies.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">أهم الشركات</p>
          <div className="space-y-1.5">
            {data.top_companies.slice(0, 3).map((company: Record<string, string | number | undefined>, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--muhide-orange)] shrink-0" />
                <span className="text-[var(--text-secondary)]">{company.name || 'شركة'}</span>
                {company.count && (
                  <span className="mr-auto text-[var(--text-muted)]">{company.count}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!data.top_contacts.length && !data.top_companies.length && data.sent === 0 && data.received === 0 && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <Mail className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-1" />
          <p className="text-xs text-[var(--text-muted)]">لا توجد بيانات بريد</p>
        </div>
      )}
    </div>
  )
}

export const EmailIntelligenceWidget = createWorkspaceWidget(
  { id: 'emailIntelligence', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.email,
  {
    metadata: { title: 'ذكاء البريد' },
    render: ({ data }) => <EmailIntelligenceView data={data} />,
  },
)
