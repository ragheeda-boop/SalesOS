'use client'

import { createWidget } from '@salesos/workspace'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecision } from '@/features/revenue-execution/_providers/DecisionProvider'
import { CompanyDNAView } from './CompanyDNAView'
import type { CompanyDNA } from '@/application/company-intelligence/company-intelligence.dto'

export const CompanyDNAWidget = createWidget({
  metadata: {
    id: 'companyDNA',
    title: 'الحمض النووي للشركة',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['company:dna:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.companyDNA.minHeight,
  },
  useData: () => {
    const { id: companyId } = useParams<{ id: string }>()
    const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
    useDecision()
    return {
      data: data?.dna ?? null,
      status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
      lastUpdated: null,
      error: error as Error | null,
      refetch,
    }
  },
  render: ({ data }) => <CompanyDNAView dna={data as CompanyDNA | null} />,
})
