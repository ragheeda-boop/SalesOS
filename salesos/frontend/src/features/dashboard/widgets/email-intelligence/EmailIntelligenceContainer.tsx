'use client'

import { createDashboardWidget } from '@salesos/widget-sdk'
import { EmailIntelligenceView } from './EmailIntelligenceView'
import type { EmailMetricsDTO } from '@/lib/api/types'

export const EmailIntelligenceWidget = createDashboardWidget<EmailMetricsDTO>(
 'emailIntelligence',
 {
 metadata: {
 title: 'ذكاء البريد الإلكتروني',
 description: 'تحليلات البريد الإلكتروني — الإرسال، الاستلام، الردود',
 permissions: ['activity:read'],
 featureFlag: { enabled: true },
 gridColumn: 'span 4',
 minHeight: '320px',
 },
 render: ({ data, status, refresh }) => (
 <EmailIntelligenceView
 metrics={data ?? null}
 isLoading={status === 'loading'}
 error={status === 'error' ? new Error('Failed to load email intelligence') : null}
 onRefresh={refresh}
 />
 ),
 },
)
