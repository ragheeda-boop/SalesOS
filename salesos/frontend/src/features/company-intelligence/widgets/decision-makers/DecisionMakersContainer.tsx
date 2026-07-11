'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { DecisionMakersView } from './DecisionMakersView'

export const DecisionMakersWidget = createWidget({
  metadata: {
    id: 'decisionMakers', title: 'صناع القرار', category: 'intelligence', priority: 'high',
    permissions: ['company:decision-makers:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.decisionMakers.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.decisionMakers },
  render: ({ data }) => <DecisionMakersView makers={data} />,
})
