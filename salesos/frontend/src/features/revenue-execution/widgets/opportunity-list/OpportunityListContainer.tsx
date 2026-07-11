'use client'

import { createWidget } from '@salesos/workspace'
import { loadOpportunities } from '@/application/revenue-execution/opportunity.store'
import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'
import { OpportunityListView } from './OpportunityListView'

export const OpportunityListWidget = createWidget({
  metadata: {
    id: 'opportunityList',
    title: 'الفرص',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['opportunity:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: '420px',
  },
  useData: () => {
    const opportunities = loadOpportunities()
    return {
      data: opportunities,
      status: 'ready',
      lastUpdated: new Date().toISOString(),
      error: null,
      refetch: () => {},
    }
  },
  render: ({ data }) => <OpportunityListView opportunities={data} />,
})
