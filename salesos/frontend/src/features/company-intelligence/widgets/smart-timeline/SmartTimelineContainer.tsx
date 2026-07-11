'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { SmartTimelineView } from './SmartTimelineView'

export const SmartTimelineWidget = createWidget({
  metadata: {
    id: 'smartTimeline', title: 'الجدول الزمني الذكي', category: 'intelligence', priority: 'high',
    permissions: ['company:timeline:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.smartTimeline.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.smartTimeline },
  render: ({ data }) => <SmartTimelineView events={data} />,
})
