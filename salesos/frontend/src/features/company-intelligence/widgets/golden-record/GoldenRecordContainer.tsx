'use client'

import { createWidget } from '@salesos/widget-sdk'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecision } from '@/features/revenue-execution/_providers/DecisionProvider'
import { GoldenRecordView } from './GoldenRecordView'
import type { GoldenRecordEntry, CompanyDNA } from '@/application/company-intelligence/company-intelligence.dto'

export const GoldenRecordWidget = createWidget({
 metadata: {
 id: 'goldenRecord', title: 'السجل الذهبي', category: 'intelligence', priority: 'low',
 permissions: ['company:golden-record:read'], featureFlag: { enabled: true },
 minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.goldenRecord.minHeight,
 },
 useData: () => {
 const { id: companyId } = useParams<{ id: string }>()
 const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
 useDecision()
 return {
 data: data ? { entries: data.goldenRecord, dna: data.dna } : null,
 status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
 lastUpdated: null,
 error: error as Error | null,
 refetch,
 }
 },
 render: ({ data }) => data ? <GoldenRecordView entries={data.entries ?? []} dna={data.dna as CompanyDNA | null} /> : null,
})
