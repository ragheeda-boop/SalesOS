'use client'

import { createDashboardWidget } from '../../sdk'
import { DecisionQueueView } from './DecisionQueueView'
import type { DecisionQueueData } from '@/application/dashboard/dashboard.dto'

export const DecisionQueueWidget = createDashboardWidget<DecisionQueueData>('decisionQueue', {
  metadata: {
    title: 'قرارات معلقة',
    description: 'القرارات التي تحتاج إلى اتخاذ إجراء',
    permissions: ['decisions:read'],
    featureFlag: { enabled: true },
  },
  render: ({ data, refresh }) => (
    <DecisionQueueView
      items={data.items ?? []}
      total={data.total ?? 0}
      onItemClick={(id) => {
        window.location.href = `/companies/${data.items?.find((i) => i.id === id)?.companyId ?? id}`
      }}
    />
  ),
})
