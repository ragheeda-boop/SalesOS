'use client'

import { createWidget } from '@salesos/workspace'
import { useOpportunities } from '@/lib/hooks/opportunityQueries'
import type { ForecastData } from './types'
import { ForecastView } from './ForecastView'

export const ForecastIntelligenceWidget = createWidget({
  metadata: { id: 'forecastIntelligence', title: 'التوقعات', category: 'intelligence', priority: 'critical', permissions: ['forecast:read'], featureFlag: { enabled: true, tier: 'enabled' }, minHeight: '320px' },
  useData: () => {
    const { data: oppsResp, isLoading, isError, error } = useOpportunities()

    if (isLoading) {
      return { data: null, status: 'loading' as const, lastUpdated: null, error: null, refetch: () => {} }
    }
    if (isError || !oppsResp) {
      return { data: null, status: 'error' as const, lastUpdated: null, error: error ?? new Error('Failed to load opportunities'), refetch: () => {} }
    }

    const opps = oppsResp.items
    const active = opps.filter((o) => !['won', 'lost'].includes(o.stage))
    const totalPipeline = active.reduce((s, o) => s + (o.value ?? 0), 0)
    const wonValue = opps.filter((o) => o.stage === 'won').reduce((s, o) => s + (o.value ?? 0), 0)

    const data: ForecastData = {
      currentQuarter: { target: 0, actual: wonValue, projected: totalPipeline, confidence: 0 },
      monthlyTrend: [],
      risks: [],
    }

    return { data, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <ForecastView data={data} />,
})
