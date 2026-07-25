'use client'

import { createDashboardWidget } from '@salesos/widget-sdk'
import { CalendarIntelligenceView } from './CalendarIntelligenceView'
import type { CalendarMetricsDTO } from '@/lib/api/types'

export const CalendarIntelligenceWidget = createDashboardWidget<CalendarMetricsDTO>(
 'calendarIntelligence',
 {
 metadata: {
 title: 'ذكاء التقويم',
 description: 'تحليلات الاجتماعات والمواعيد',
 permissions: ['activity:read'],
 featureFlag: { enabled: true },
 gridColumn: 'span 4',
 minHeight: '320px',
 },
 render: ({ data, status, refresh }) => (
 <CalendarIntelligenceView
 metrics={data ?? null}
 isLoading={status === 'loading'}
 error={status === 'error' ? new Error('Failed to load calendar intelligence') : null}
 onRefresh={refresh}
 />
 ),
 },
)
