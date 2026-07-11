'use client'

import { useMemo } from 'react'
import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext } from '../../../company-intelligence/index'
import { deriveNextBestAction } from '@/application/revenue-execution/nba.engine'
import type { NextBestAction } from '@/application/revenue-execution/nba.dto'
import { NBAView } from './NBAView'

export const NextBestActionWidget = createWidget({
  metadata: {
    id: 'nextBestAction',
    title: 'أفضل إجراء تالي',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['company:nba:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: '420px',
  },
  useData: () => {
    const ctx = useCompanyIntelligenceContext()
    const action = useMemo(() => deriveNextBestAction(
      ctx.widgets.companyDNA.data,
      ctx.widgets.aiRecommendation.data,
      ctx.widgets.smartTimeline.data,
      ctx.widgets.signalsFeed.data,
      ctx.widgets.decisionMakers.data,
    ), [ctx.widgets.companyDNA.data, ctx.widgets.aiRecommendation.data, ctx.widgets.smartTimeline.data, ctx.widgets.signalsFeed.data, ctx.widgets.decisionMakers.data])

    return {
      data: action,
      status: ctx.widgets.companyDNA.status,
      lastUpdated: ctx.widgets.companyDNA.lastUpdated,
      error: ctx.widgets.companyDNA.error,
      refetch: ctx.refetch,
    }
  },
  render: ({ data }) => <NBAView action={data} onExecute={(a) => console.log('Execute:', a)} />,
})
