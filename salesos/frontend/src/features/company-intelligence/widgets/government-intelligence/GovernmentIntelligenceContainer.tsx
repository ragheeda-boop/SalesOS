'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { GovernmentIntelligenceView } from './GovernmentIntelligenceView'

export const GovernmentIntelligenceWidget = createWidget({
  metadata: {
    id: 'governmentIntelligence', title: 'البيانات الحكومية', category: 'intelligence', priority: 'medium',
    permissions: ['company:government:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.governmentIntelligence.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.governmentIntelligence },
  render: ({ data }) => <GovernmentIntelligenceView records={data} />,
})
