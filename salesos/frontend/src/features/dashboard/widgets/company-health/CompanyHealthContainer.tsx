'use client'

import { createDecisionEnabledWidget } from '../../sdk'
import { CompanyHealthView } from './CompanyHealthView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'
import type { CompanyHealthData } from './types'

export const CompanyHealthWidget = createDecisionEnabledWidget<CompanyHealthData>('companyHealth', {
  metadata: {
    title: 'صحة الشركة',
    description: 'مؤشرات الأداء الرئيسية وتنبيهات الشركة',
    permissions: ['company:read'],
    featureFlag: { enabled: true },
  },
  useDecision: (tenantId) => useCompanyDecision(tenantId),
  useNBA: () => useNBAFeed(),
  render: (ctx) => (
    <CompanyHealthView
      overallScore={ctx.data.overallScore}
      metrics={ctx.data.metrics ?? []}
      alerts={ctx.data.alerts ?? []}
      companyName={ctx.data.companyName}
      decision={ctx.decision}
      nbaItems={ctx.nbaItems}
      isDecisionLoading={ctx.isDecisionLoading}
      onAlertClick={(alertId) => {
        const alert = ctx.data.alerts?.find((a) => a.id === alertId)
        if (alert?.companyId) {
          window.location.href = `/companies/${alert.companyId}`
        }
      }}
    />
  ),
})
