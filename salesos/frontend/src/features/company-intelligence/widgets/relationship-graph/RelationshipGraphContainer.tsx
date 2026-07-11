'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { RelationshipGraphView } from './RelationshipGraphView'

export const RelationshipGraphWidget = createWidget({
  metadata: {
    id: 'relationshipGraph', title: 'العلاقات', category: 'intelligence', priority: 'high',
    permissions: ['company:graph:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.relationshipGraph.minHeight,
  },
  useData: () => { const ctx = useCompanyIntelligenceContext(); return ctx.widgets.relationshipGraph },
  render: ({ data }) => data ? <RelationshipGraphView nodes={data.nodes} edges={data.edges} /> : null,
})
