'use client'

import { createWidget } from '@salesos/workspace'
import type { EmailSummary } from '@/application/revenue-execution/email.dto'
import { EmailView } from './EmailView'

const sampleEmails: EmailSummary[] = [
  { threadId: 'e1', subject: 'متابعة عرض الطاقة المتجددة', summary: 'العميل يطلب معلومات إضافية عن حلول الطاقة الشمسية', sender: 'أحمد السلمي', date: '2026-07-10', priority: 'high', suggestedReply: 'شكراً لتواصلكم. يمكننا ترتيب عرض توضيحي الأسبوع القادم.', actionItems: ['ترتيب عرض توضيحي', 'إرسال كتيب المنتج'], relatesTo: { entityType: 'company', entityId: 'c1', entityName: 'شركة الطاقة' } },
  { threadId: 'e2', subject: 'تأكيد موعد الاجتماع', summary: 'تأكيد موعد اجتماع الخميس الساعة 10 صباحاً', sender: 'نورة القحطاني', date: '2026-07-09', priority: 'medium', actionItems: ['تجهيز العرض التقديمي'] },
]

export const EmailIntelligenceWidget = createWidget({
  metadata: { id: 'emailIntelligence', title: 'ذكاء البريد', category: 'intelligence', priority: 'high', permissions: ['email:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sampleEmails, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <EmailView emails={data} />,
})
