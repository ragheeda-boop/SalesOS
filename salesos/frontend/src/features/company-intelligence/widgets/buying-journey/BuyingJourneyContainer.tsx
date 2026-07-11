'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { BuyingJourneyView } from './BuyingJourneyView'

export const BuyingJourneyWidget = createWidget({
  metadata: {
    id: 'buyingJourney', title: 'رحلة الشراء', category: 'intelligence', priority: 'medium',
    permissions: ['company:buying-journey:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.buyingJourney.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.buyingJourney },
  render: ({ data }) => <BuyingJourneyView journey={data} />,
})
