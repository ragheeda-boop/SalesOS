'use client'

import { createWidget } from '@salesos/workspace'
import { loadOpportunities } from '@/application/revenue-execution/opportunity.store'
import type { ForecastData } from './types'
import { ForecastView } from './ForecastView'

export const ForecastIntelligenceWidget = createWidget({
  metadata: { id: 'forecastIntelligence', title: 'التوقعات', category: 'intelligence', priority: 'critical', permissions: ['forecast:read'], featureFlag: { enabled: true, tier: 'enabled' }, minHeight: '320px' },
  useData: () => {
    const opps = loadOpportunities()
    const active = opps.filter((o) => !['won', 'lost'].includes(o.stage))
    const totalPipeline = active.reduce((s, o) => s + o.estimatedValue, 0)
    const data: ForecastData = {
      currentQuarter: { target: 10000000, actual: 4200000, projected: 7800000, confidence: 0.78 },
      monthlyTrend: [{ month: 'يونيو', actual: 1200000, forecast: 1100000 }, { month: 'يوليو', actual: 1500000, forecast: 1400000 }],
      risks: [{ label: 'تباطؤ في قطاع الطاقة', impact: 500000, probability: 0.35 }, { label: 'تأخير في توقيع العقود', impact: 300000, probability: 0.25 }],
    }
    return { data, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <ForecastView data={data} />,
})
