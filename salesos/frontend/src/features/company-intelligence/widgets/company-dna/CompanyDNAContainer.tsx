'use client'

import { createWidget } from '@salesos/widget-sdk'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecisionScores } from '@/lib/decisionQueries'
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
 const { data: decisionScores } = useDecisionScores(companyId, 'company')
 const dna = data?.dna ?? null
 return {
 data: dna ? { ...dna, decisionScores: decisionScores ?? [] } : null,
 status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
 lastUpdated: null,
 error: error as Error | null,
 refetch,
 }
 },
 render: ({ data }) => <CompanyDNAView dna={data as CompanyDNA | null} />,
})
