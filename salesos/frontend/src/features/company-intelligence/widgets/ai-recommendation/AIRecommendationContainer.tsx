'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { AIRecommendationView } from './AIRecommendationView'

export const AIRecommendationWidget = createWidget({
  metadata: {
    id: 'aiRecommendation', title: 'توصيات AI', category: 'intelligence', priority: 'critical',
    permissions: ['company:ai:recommendations'], featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.aiRecommendation.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.aiRecommendation },
  render: ({ data }) => <AIRecommendationView recommendation={data} />,
})
