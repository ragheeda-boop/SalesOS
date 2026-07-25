'use client'

import { createDashboardWidget } from '@salesos/widget-sdk'
import { FollowupCenterView } from './FollowupCenterView'
import type { FollowupDashboardDTO } from '@/lib/api/types'

export const FollowupCenterWidget = createDashboardWidget<FollowupDashboardDTO>(
 'followupCenter',
 {
 metadata: {
 title: 'مركز المتابعة',
 description: 'قائمة المتابعات المطلوبة والمتأخرة',
 permissions: ['activity:read'],
 featureFlag: { enabled: true },
 gridColumn: 'span 4',
 minHeight: '400px',
 },
 render: ({ data, status, refresh }) => (
 <FollowupCenterView
 followups={data ?? null}
 isLoading={status === 'loading'}
 error={status === 'error' ? new Error('Failed to load follow-ups') : null}
 onRefresh={refresh}
 />
 ),
 },
)
