'use client'

import { createDashboardWidget } from '../../sdk'
import { IntelligenceFeedView } from './IntelligenceFeedView'
import type { IntelligenceFeedData } from '@/application/dashboard/dashboard.dto'

export const IntelligenceFeedWidget = createDashboardWidget<IntelligenceFeedData>('intelligenceFeed', {
  metadata: {
    title: 'Intelligence Feed',
    description: 'الإشارات الذكية والتنبيهات التنافسية',
    permissions: ['intelligence:read'],
    featureFlag: { enabled: true },
  },
  render({ data }) {
    return (
      <IntelligenceFeedView
        items={data.items ?? []}
        total={data.total ?? 0}
        unseenCount={data.unseenCount ?? 0}
      />
    )
  },
})
