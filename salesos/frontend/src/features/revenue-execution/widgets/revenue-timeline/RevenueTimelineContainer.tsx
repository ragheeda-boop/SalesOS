'use client'

import { useMemo } from 'react'
import { createWidget } from '@salesos/workspace'
import { useOpportunities } from '@/lib/hooks/opportunityQueries'
import { useTasks } from '@/lib/hooks/taskQueries'
import type { RevenueTimelineEvent } from './types'

export const RevenueTimelineWidget = createWidget({
  metadata: { id: 'revenueTimeline', title: 'الجدول الزمني للإيرادات', category: 'intelligence', priority: 'medium', permissions: ['revenue:timeline:read'], featureFlag: { enabled: true }, minHeight: '400px' },
  useData: () => {
    const { data: opportunitiesData, isLoading: oppsLoading, error: oppsError } = useOpportunities()
    const { data: tasksData, isLoading: tasksLoading, error: tasksError } = useTasks()

    const events: RevenueTimelineEvent[] = useMemo(() => {
      const result: RevenueTimelineEvent[] = []
      if (tasksData) {
        for (const t of tasksData) {
          result.push({ id: `task_${t.id}`, type: 'task', summary: t.title, date: t.created_at ?? '', entityName: t.company_id ?? undefined })
        }
      }
      if (opportunitiesData?.items) {
        for (const o of opportunitiesData.items) {
          result.push({ id: `deal_${o.id}`, type: 'deal', summary: o.name, date: o.expected_close_date ?? '', entityName: o.company_name, value: o.value })
        }
      }
      return result
    }, [tasksData, opportunitiesData])

    return {
      data: events,
      status: oppsLoading || tasksLoading ? 'loading' : 'ready',
      lastUpdated: new Date().toISOString(),
      error: oppsError || tasksError,
      refetch: () => {},
    }
  },
  render: ({ data }) => <RevenueTimelineView events={data} />,
})
