'use client'

import { createWidget } from '@salesos/workspace'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecision } from '@/features/revenue-execution/_providers/DecisionProvider'
import { GovernmentIntelligenceView } from './GovernmentIntelligenceView'
import type { GovernmentRecord } from '@/application/company-intelligence/company-intelligence.dto'

export const GovernmentIntelligenceWidget = createWidget({
  metadata: {
    id: 'governmentIntelligence', title: 'البيانات الحكومية', category: 'intelligence', priority: 'medium',
    permissions: ['company:government:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.governmentIntelligence.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>()
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
    useDecision()
    return {
      data: data?.government ?? null,
      status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    }
  },
  render: ({ data }) => <GovernmentIntelligenceView records={(data ?? []) as GovernmentRecord[]} />,
})
