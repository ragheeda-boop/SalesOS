'use client'

import { createWidget } from '@salesos/widget-sdk'
import { useParams } from 'next/navigation'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { useDecisionSafe } from '@/features/revenue-execution/_providers/DecisionProvider'
import { AIRecommendationView } from './AIRecommendationView'
import type { AIRecommendation } from '@/application/company-intelligence/company-intelligence.dto'

export const AIRecommendationWidget = createWidget({
 metadata: {
 id: 'aiRecommendation', title: 'توصيات AI', category: 'intelligence', priority: 'critical',
 permissions: ['company:ai:recommendations'], featureFlag: { enabled: true, tier: 'enabled' },
 minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.aiRecommendation.minHeight,
 },
 useData: () => {
 const { id: companyId } = useParams<{ id: string }>()
 const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
  useDecisionSafe()
 return {
 data: data?.aiRecommendation ?? null,
 status: isLoading ? 'loading' as const : isError ? 'error' as const : 'ready' as const,
 lastUpdated: null,
 error: error as Error | null,
 refetch,
 }
 },
 render: ({ data }) => <AIRecommendationView recommendation={data as AIRecommendation | null} />,
})
