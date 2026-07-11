'use client'

import { createDashboardWidget } from '../../sdk'
import { RecentActivityView } from './RecentActivityView'
import type { RecentActivityData } from '@/application/dashboard/dashboard.dto'

export const RecentActivityWidget = createDashboardWidget<RecentActivityData>('recentActivity', {
  metadata: {
    title: 'نشاطات حديثة',
    description: 'آخر النشاطات على الشركات المتابعة',
    permissions: ['activity:read'],
    featureFlag: { enabled: true },
  },
  render: ({ data, refresh }) => (
    <RecentActivityView
      items={data.items ?? []}
      total={data.total ?? 0}
      onItemClick={(id) => {
        const item = data.items?.find((i) => i.id === id)
        if (item?.companyId) {
          window.location.href = `/companies/${item.companyId}`
        }
      }}
    />
  ),
})
