'use client'

import { createDashboardWidget } from '../../sdk'
import { MarketPulseView } from './MarketPulseView'
import type { MarketPulseData } from '@/application/dashboard/dashboard.dto'

export const MarketPulseWidget = createDashboardWidget<MarketPulseData>('marketPulse', {
  metadata: {
    title: 'نبض السوق',
    description: 'اتجاهات السوق وشركات ذات التحركات البارزة',
    permissions: ['market:read'],
    featureFlag: { enabled: true, tier: 'enterprise' },
  },
  render: ({ data }) => (
    <MarketPulseView
      trends={data.trends ?? []}
      topMovers={data.topMovers ?? []}
      onTrendClick={(name) => {
        window.location.href = `/market/trends/${encodeURIComponent(name)}`
      }}
      onMoverClick={(companyId) => {
        window.location.href = `/companies/${companyId}`
      }}
    />
  ),
})
