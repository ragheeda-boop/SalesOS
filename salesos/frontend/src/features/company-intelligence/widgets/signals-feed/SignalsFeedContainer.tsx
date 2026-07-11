'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { SignalsFeedView } from './SignalsFeedView'

export const SignalsFeedWidget = createWidget({
  metadata: {
    id: 'signalsFeed', title: 'الإشارات', category: 'intelligence', priority: 'high',
    permissions: ['company:signals:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.signalsFeed.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.signalsFeed },
  render: ({ data }) => <SignalsFeedView signals={data} />,
})
