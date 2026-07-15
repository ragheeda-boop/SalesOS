'use client'

import { createWidget } from '@salesos/workspace'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecision } from '@/features/revenue-execution/_providers/DecisionProvider'
import { DecisionMakersView } from './DecisionMakersView'
import type { DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'

export const DecisionMakersWidget = createWidget({
  metadata: {
    id: 'decisionMakers', title: 'صناع القرار', category: 'intelligence', priority: 'high',
    permissions: ['company:decision-makers:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.decisionMakers.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>()
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
    useDecision()
    return {
      data: data?.decisionMakers ?? null,
      status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    }
  },
  render: ({ data }) => <DecisionMakersView makers={(data ?? []) as DecisionMaker[]} />,
})
