'use client'

import { createWidget } from '@salesos/workspace'
import { loadTasks } from '@/application/revenue-execution/task.store'
import { loadOpportunities } from '@/application/revenue-execution/opportunity.store'
import type { RevenueTimelineEvent } from './types'

export const RevenueTimelineWidget = createWidget({
  metadata: { id: 'revenueTimeline', title: 'الجدول الزمني للإيرادات', category: 'intelligence', priority: 'medium', permissions: ['revenue:timeline:read'], featureFlag: { enabled: true }, minHeight: '400px' },
  useData: () => {
    const events: RevenueTimelineEvent[] = [
      ...loadTasks().map((t) => ({ id: `task_${t.id}`, type: 'task' as const, summary: t.title, date: t.createdAt, entityName: t.companyName })),
      ...loadOpportunities().map((o) => ({ id: `deal_${o.id}`, type: 'deal' as const, summary: o.title, date: o.createdAt, entityName: o.companyName, value: o.estimatedValue })),
    ]
    return { data: events, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <RevenueTimelineView events={data} />,
})
