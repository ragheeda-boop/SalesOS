'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { DocumentIntelligenceView } from './DocumentIntelligenceView'

export const DocumentIntelligenceWidget = createWidget({
  metadata: {
    id: 'documentIntelligence', title: 'المستندات', category: 'intelligence', priority: 'medium',
    permissions: ['company:documents:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.documentIntelligence.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.documentIntelligence },
  render: ({ data }) => <DocumentIntelligenceView documents={data} />,
})
