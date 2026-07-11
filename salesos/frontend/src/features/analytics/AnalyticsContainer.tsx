'use client'

import { createWidget } from '@salesos/workspace'
import type { AnalyticsData } from './types'
import { AnalyticsView } from './AnalyticsView'

const sample: AnalyticsData = {
  users: { total: 15, active: 12, new: 3 },
  usage: { totalSessions: 342, avgSessionDuration: 840, dailyActiveUsers: 12 },
  pipeline: { totalValue: 8500000, weightedValue: 4200000, dealCount: 24, winRate: 0.33 },
  widgets: {
    mostUsed: 'company-dna', usageCount: 120,
    widgets: [
      { id: 'company-dna', name: 'Company DNA', count: 120 },
      { id: 'nba', name: 'NBA Engine', count: 98 },
      { id: 'search', name: 'Search', count: 85 },
      { id: 'pipeline', name: 'Pipeline', count: 72 },
      { id: 'timeline', name: 'Timeline', count: 65 },
      { id: 'opportunity-list', name: 'الفرص', count: 55 },
    ],
  },
  search: { totalQueries: 420, avgResults: 12, topQueries: ['شركات الطاقة', 'مستشفيات الرياض', 'مقاولات'] },
  nba: { shown: 85, executed: 38, acceptanceRate: 45 },
}

export const CommercialAnalyticsWidget = createWidget({
  metadata: { id: 'commercialAnalytics', title: 'تحليلات المنتج', category: 'intelligence', priority: 'critical', permissions: ['analytics:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '600px' },
  useData: () => ({
    data: sample, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {},
  }),
  render: ({ data }) => <AnalyticsView data={data} />,
})
