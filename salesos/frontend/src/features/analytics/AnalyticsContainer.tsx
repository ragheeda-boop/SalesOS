'use client'

import { createWidget } from '@salesos/widget-sdk'
import type { AnalyticsData } from './types'
import { AnalyticsView } from './AnalyticsView'

/** Honest empty — commercial analytics widget is not wired to live APIs. */
const empty: AnalyticsData = {
 users: { total: 0, active: 0, new: 0 },
 usage: { totalSessions: 0, avgSessionDuration: 0, dailyActiveUsers: 0 },
 pipeline: { totalValue: 0, weightedValue: 0, dealCount: 0, winRate: 0 },
 widgets: { mostUsed: '', usageCount: 0, widgets: [] },
 search: { totalQueries: 0, avgResults: 0, topQueries: [] },
 nba: { shown: 0, executed: 0, acceptanceRate: 0 },
}

export const CommercialAnalyticsWidget = createWidget({
 metadata: { id: 'commercialAnalytics', title: 'تحليلات المنتج', category: 'intelligence', priority: 'critical', permissions: ['analytics:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '600px' },
 useData: () => ({
 data: empty, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {},
 }),
 render: ({ data }) => <AnalyticsView data={data} />,
})
