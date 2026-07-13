'use client'

import { createDecisionEnabledWidget } from '../../sdk'
import { DecisionQueueView } from './DecisionQueueView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'
import type { DecisionQueueData } from '@/application/dashboard/dashboard.dto'

export const DecisionQueueWidget = createDecisionEnabledWidget<DecisionQueueData>('decisionQueue', {
  metadata: {
    title: 'قرارات معلقة',
    description: 'القرارات التي تحتاج إلى اتخاذ إجراء',
    permissions: ['decisions:read'],
    featureFlag: { enabled: true },
  },
  useDecision: (tenantId) => useCompanyDecision(tenantId),
  useNBA: () => useNBAFeed(),
  render: (ctx) => (
    <DecisionQueueView
      items={ctx.data.items ?? []}
      total={ctx.data.total ?? 0}
      decision={ctx.decision}
      nbaItems={ctx.nbaItems}
      isDecisionLoading={ctx.isDecisionLoading}
      onItemClick={(id) => {
        window.location.href = `/companies/${ctx.data.items?.find((i) => i.id === id)?.companyId ?? id}`
      }}
    />
  ),
})
