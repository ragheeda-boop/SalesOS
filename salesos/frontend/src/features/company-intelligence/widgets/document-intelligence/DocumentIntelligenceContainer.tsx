'use client'

import { createWidget } from '@salesos/workspace'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecision } from '@/features/revenue-execution/_providers/DecisionProvider'
import { DocumentIntelligenceView } from './DocumentIntelligenceView'
import type { DocumentItem } from '@/application/company-intelligence/company-intelligence.dto'

export const DocumentIntelligenceWidget = createWidget({
  metadata: {
    id: 'documentIntelligence', title: 'المستندات', category: 'intelligence', priority: 'medium',
    permissions: ['company:documents:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.documentIntelligence.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>()
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
    useDecision()
    return {
      data: data?.documents ?? null,
      status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    }
  },
  render: ({ data }) => <DocumentIntelligenceView documents={(data ?? []) as DocumentItem[]} />,
})
