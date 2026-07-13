'use client'

import { createWidget } from '@salesos/workspace'
import { useOpportunities } from '@/lib/hooks/opportunityQueries'
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
    const { data, isLoading, error, refetch } = useOpportunities()
    return {
      data: (data?.items ?? []) as unknown as RevenueOpportunity[],
      status: isLoading ? 'loading' as const : error ? 'error' as const : 'ready' as const,
      lastUpdated: data ? new Date().toISOString() : null,
      error: error ?? null,
      refetch,
    }
  },
  render: ({ data }) => <OpportunityListView opportunities={data} />,
})
