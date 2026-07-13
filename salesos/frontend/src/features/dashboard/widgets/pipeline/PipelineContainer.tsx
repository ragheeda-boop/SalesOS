'use client'

import { createDecisionEnabledWidget } from '../../sdk'
import { PipelineView } from './PipelineView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'
import type { PipelineData } from './types'

export const PipelineWidget = createDecisionEnabledWidget<PipelineData>('pipeline', {
  metadata: {
    title: 'أنابيب المبيعات',
    description: 'مراحل الأنبوب والصفقات النشطة',
    permissions: ['pipeline:read'],
    featureFlag: { enabled: true },
  },
  useDecision: (tenantId) => useCompanyDecision(tenantId),
  useNBA: () => useNBAFeed(),
  render: (ctx) => (
    <PipelineView
      stages={ctx.data.stages ?? []}
      deals={ctx.data.deals ?? []}
      totalValue={ctx.data.totalValue ?? 0}
      dealCount={ctx.data.dealCount ?? 0}
      decision={ctx.decision}
      nbaItems={ctx.nbaItems}
      isDecisionLoading={ctx.isDecisionLoading}
      onDealClick={(dealId) => {
        window.location.href = `/companies/${ctx.data.deals?.find((d) => d.id === dealId)?.companyId ?? dealId}`
      }}
    />
  ),
})
