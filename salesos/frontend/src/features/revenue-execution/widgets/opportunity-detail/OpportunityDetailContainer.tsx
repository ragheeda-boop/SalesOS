'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'
import type { DecisionResult } from '@salesos/decision-platform'

function mapToOpportunity(result: DecisionResult): RevenueOpportunity {
  const confidenceScore = result.scores.find(s => s.type === 'confidence')?.value ?? 0.5
  const revenueScore = result.scores.find(s => s.type === 'revenue')

  return {
    id: result.decisionId ?? 'opp-1',
    companyId: (result.evidence[0]?.id as string) ?? 'c1',
    companyName: result.explainability?.why?.split(' ')[0] ?? 'الشركة',
    title: result.recommendation?.actionLabel ?? result.action,
    source: 'nba' as const,
    estimatedValue: revenueScore?.value != null ? Math.round(revenueScore.value * 1000000) : 500000,
    confidence: confidenceScore,
    winProbability: confidenceScore,
    stage: 'developing',
    createdAt: new Date().toISOString().split('T')[0],
    buyingIntent: result.scores.find(s => s.type === 'intent')?.value ?? 0.5,
    relationshipStrength: result.scores.find(s => s.type === 'relationship')?.value ?? 0.5,
    riskLevel: confidenceScore < 0.4 ? 'high' : confidenceScore < 0.7 ? 'medium' : 'low',
    tags: [],
    notes: [],
    lastActivityAt: new Date().toISOString(),
  }
}

export const OpportunityDetailWidget = createWidget({
  metadata: {
    id: 'opportunityDetail',
    title: 'تفاصيل الفرصة',
    category: 'intelligence',
    priority: 'high',
    permissions: ['opportunity:read'],
    featureFlag: { enabled: true },
    minHeight: '320px',
  },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: RevenueOpportunity | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.getRecommendation('', '', '')
        const data = mapToOpportunity(result)
        setState({ data, status: 'ready', lastUpdated: new Date().toISOString(), error: null })
      } catch (err) {
        setState(prev => ({ ...prev, status: 'error', error: err instanceof Error ? err : new Error(String(err)) }))
      }
    }, [decision])

    useEffect(() => { fetchData() }, [fetchData])

    return {
      data: state.data,
      status: state.status,
      lastUpdated: state.lastUpdated,
      error: state.error,
      refetch: fetchData,
    }
  },
  render: ({ data }) => null,
})