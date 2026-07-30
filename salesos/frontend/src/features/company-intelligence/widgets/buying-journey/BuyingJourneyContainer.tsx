'use client'

import { createWidget } from '@salesos/widget-sdk'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecisionSafe } from '@/features/revenue-execution/_providers/DecisionProvider'
import { BuyingJourneyView } from './BuyingJourneyView'
import type { BuyingJourney } from '@/application/company-intelligence/company-intelligence.dto'

export const BuyingJourneyWidget = createWidget({
 metadata: {
 id: 'buyingJourney', title: 'رحلة الشراء', category: 'intelligence', priority: 'medium',
 permissions: ['company:buying-journey:read'], featureFlag: { enabled: true },
 minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.buyingJourney.minHeight,
 },
 useData: () => {
 const { id: companyId } = useParams<{ id: string }>()
 const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
  useDecisionSafe()
 return {
 data: data?.buyingJourney ?? null,
 status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
 lastUpdated: null,
 error: error as Error | null,
 refetch,
 }
 },
 render: ({ data }) => <BuyingJourneyView journey={data as BuyingJourney | null} />,
})
