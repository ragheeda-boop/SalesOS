'use client'

import { createWidget } from '@salesos/workspace'
import { loadOpportunities } from '@/application/revenue-execution/opportunity.store'
import type { PipelineInsight, PipelineStage, StalledDeal } from '@/application/revenue-execution/pipeline.dto'
import { STAGE_LABEL, type OpportunityStage } from '@/application/revenue-execution/opportunity.dto'
import { PipelineView } from './PipelineView'

const STAGE_COLORS: Record<string, string> = {
  identified: 'bg-neutral-300 dark:bg-neutral-600',
  qualifying: 'bg-blue-400 dark:bg-blue-600',
  developing: 'bg-purple-400 dark:bg-purple-600',
  proposing: 'bg-amber-400 dark:bg-amber-600',
  negotiating: 'bg-orange-400 dark:bg-orange-600',
  closing: 'bg-red-400 dark:bg-red-600',
}

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
    const opps = loadOpportunities()
    const active = opps.filter((o) => !['won', 'lost'].includes(o.stage))
    const stages: PipelineStage[] = (['identified', 'qualifying', 'developing', 'proposing', 'negotiating', 'closing'] as OpportunityStage[]).map((s) => ({
      id: s,
      label: STAGE_LABEL[s],
      deals: active.filter((o) => o.stage === s).length,
      value: active.filter((o) => o.stage === s).reduce((sum, o) => sum + o.estimatedValue, 0),
      color: STAGE_COLORS[s] ?? 'bg-neutral-300',
    }))
    const totalValue = stages.reduce((s, st) => s + st.value, 0)
    const totalDeals = stages.reduce((s, st) => s + st.deals, 0)

    const stalled: StalledDeal[] = active
      .filter((o) => o.lastActivityAt && (Date.now() - new Date(o.lastActivityAt).getTime()) > 14 * 24 * 60 * 60 * 1000)
      .map((o) => ({
        id: o.id,
        companyName: o.companyName,
        title: o.title,
        stage: STAGE_LABEL[o.stage],
        value: o.estimatedValue,
        daysStalled: Math.floor((Date.now() - new Date(o.lastActivityAt!).getTime()) / (24 * 60 * 60 * 1000)),
      }))

    const pipeline: PipelineInsight = {
      totalDeals,
      totalValue,
      weightedValue: stages.reduce((s, st) => s + st.value * [0.1, 0.25, 0.45, 0.65, 0.8, 0.9][stages.indexOf(st)], 0),
      avgDealSize: totalDeals > 0 ? totalValue / totalDeals : 0,
      winRate: opps.length > 0 ? opps.filter((o) => o.stage === 'won').length / opps.length : 0,
      stages,
      stalledDeals: stalled,
      bottlenecks: stages.filter((s) => s.deals > 0).map((s) => ({ stage: s.label, deals: s.deals, avgDays: 30 })),
    }

    return { data: pipeline, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <PipelineView pipeline={data} />,
})
