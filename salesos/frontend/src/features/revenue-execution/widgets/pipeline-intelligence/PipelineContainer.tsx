'use client'

import { createWidget } from '@salesos/workspace'
import { useOpportunities } from '@/lib/hooks/opportunityQueries'
import { useDecisionScores } from '@/lib/decisionQueries'
import { STAGE_LABEL, STAGE_WEIGHT } from '@/application/revenue-execution/opportunity.dto'
import type { PipelineInsight, PipelineStage } from '@/application/revenue-execution/pipeline.dto'
import { PipelineView } from './PipelineView'

const STAGE_COLORS: Record<string, string> = {
  identified: 'bg-neutral-300 dark:bg-neutral-600',
  qualifying: 'bg-blue-400 dark:bg-blue-600',
  developing: 'bg-purple-400 dark:bg-purple-600',
  proposing: 'bg-amber-400 dark:bg-amber-600',
  negotiating: 'bg-orange-400 dark:bg-orange-600',
  closing: 'bg-red-400 dark:bg-red-600',
}

const STAGE_ORDER = ['identified', 'qualifying', 'developing', 'proposing', 'negotiating', 'closing'] as const

export const PipelineIntelligenceWidget = createWidget({
  metadata: {
    id: 'pipelineIntelligence',
    title: 'ذكاء الأنابيب',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['pipeline:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: '400px',
  },
  useData: () => {
    const { data: oppsResp, isLoading, isError, error } = useOpportunities()
    useDecisionScores('pipeline', 'pipeline')

    if (isLoading) {
      return { data: null, status: 'loading' as const, lastUpdated: null, error: null, refetch: () => {} }
    }
    if (isError || !oppsResp) {
      return { data: null, status: 'error' as const, lastUpdated: null, error: error ?? new Error('Failed to load opportunities'), refetch: () => {} }
    }

    const opps = oppsResp.items
    const active = opps.filter((o) => !['won', 'lost'].includes(o.stage))

    const stages: PipelineStage[] = STAGE_ORDER.map((s) => ({
      id: s,
      label: STAGE_LABEL[s],
      deals: active.filter((o) => o.stage === s).length,
      value: active.filter((o) => o.stage === s).reduce((sum, o) => sum + (o.value ?? 0), 0),
      color: STAGE_COLORS[s] ?? 'bg-neutral-300',
    }))

    const totalValue = stages.reduce((s, st) => s + st.value, 0)
    const totalDeals = stages.reduce((s, st) => s + st.deals, 0)

    const pipeline: PipelineInsight = {
      totalDeals,
      totalValue,
      weightedValue: stages.reduce((s, st) => s + st.value * (STAGE_WEIGHT[st.id as keyof typeof STAGE_WEIGHT] ?? 0), 0),
      avgDealSize: totalDeals > 0 ? totalValue / totalDeals : 0,
      winRate: opps.length > 0 ? opps.filter((o) => o.stage === 'won').length / opps.length : 0,
      stages,
      stalledDeals: [],
      bottlenecks: [],
    }

    return { data: pipeline, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <PipelineView pipeline={data} />,
})
