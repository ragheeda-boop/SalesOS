'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { DecisionResult } from '@salesos/decision-platform'
import type { NextBestAction } from '@/application/revenue-execution/nba.dto'
import { NBAView } from './NBAView'

function mapDecisionToNBA(result: DecisionResult): NextBestAction {
  const score = result.scores.find(s => s.type === 'confidence')?.value ?? 0.5
  const revScore = result.scores.find(s => s.type === 'revenue')

  return {
    actionId: result.decisionId,
    actionLabel: result.recommendation.actionLabel,
    actionType: result.recommendation.action as NextBestAction['actionType'],
    reasoning: result.recommendation.reason,
    confidence: result.recommendation.confidence,
    priority: score >= 0.8 ? 'critical' : score >= 0.6 ? 'high' : score >= 0.4 ? 'medium' : 'low',
    score,
    expectedRevenue: result.explainability.expectedImpact.revenue,
    expectedImpact: score >= 0.7 ? 'high' : score >= 0.4 ? 'medium' : 'low',
    estimatedTime: result.recommendation.expectedTime ?? '—',
    contextSummary: result.explainability.why,
    triggerEvent: result.evidence[0]?.description,
    risks: result.recommendation.risks.map(r => r.description),
    alternatives: result.recommendation.alternatives.map(a => ({
      actionLabel: a.actionLabel,
      confidence: a.confidence,
    })),
    createsOpportunity: score >= 0.4,
    scoreBreakdown: {
      buyingIntent: result.scores.find(s => s.type === 'intent')?.value ?? 0,
      relationshipStrength: result.scores.find(s => s.type === 'relationship')?.value ?? 0,
      signalRecency: result.scores.find(s => s.type === 'confidence')?.factors.find(f => f.name === 'evidence_strength')?.value ?? 0,
      aiConfidence: result.recommendation.confidence,
      decisionMakerAccess: 0,
      revenuePotential: revScore?.value ?? 0,
    },
  }
}

function NBAWidgetInner({ action }: { action: NextBestAction }) {
  const decision = useDecision()

  const handleExecute = useCallback(async (a: NextBestAction) => {
    await decision.submitFeedback({
      decisionId: a.actionId,
      tenantId: '',
      actorId: '',
      outcome: 'accepted',
      timestamp: new Date().toISOString(),
      revenueImpact: a.expectedRevenue,
    })
  }, [decision])

  return <NBAView action={action} onExecute={handleExecute} />
}

export const NextBestActionWidget = createWidget({
  metadata: {
    id: 'nextBestAction',
    title: 'أفضل إجراء تالي',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['company:nba:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: '420px',
  },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{
      data: NextBestAction | null
      status: 'loading' | 'ready' | 'error'
      lastUpdated: string | null
      error: Error | null
    }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchRecommendation = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.getRecommendation('', '', '')
        const action = mapDecisionToNBA(result)
        setState({ data: action, status: 'ready', lastUpdated: new Date().toISOString(), error: null })
      } catch (err) {
        setState(prev => ({ ...prev, status: 'error', error: err instanceof Error ? err : new Error(String(err)) }))
      }
    }, [decision])

    useEffect(() => { fetchRecommendation() }, [fetchRecommendation])

    return {
      data: state.data,
      status: state.status,
      lastUpdated: state.lastUpdated,
      error: state.error,
      refetch: fetchRecommendation,
    }
  },
  render: ({ data }) => <NBAWidgetInner action={data} />,
})
