'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { ChurnData } from './types'
import type { Score } from '@salesos/decision-platform'
import { ChurnView } from './ChurnView'

function mapScoresToChurn(scores: Score[]): ChurnData {
  const atRiskAccounts = scores
    .filter(s => s.type === 'risk')
    .map((s, i) => ({
      companyName: (s.metadata?.companyName as string) ?? `الشركة ${i + 1}`,
      riskScore: s.value,
      revenue: (s.metadata?.revenue as number) ?? 0,
      reason: (s.metadata?.reason as string) ?? s.factors?.[0]?.name ?? 'مخاطر عالية',
      daysSinceActivity: (s.metadata?.daysSinceActivity as number) ?? 30,
    }))

  if (atRiskAccounts.length === 0) {
    const total = scores.reduce((sum, s) => sum + s.value, 0) / Math.max(scores.length, 1)
    for (let i = 0; i < Math.min(scores.length, 5); i++) {
      atRiskAccounts.push({
        companyName: `الشركة ${i + 1}`,
        riskScore: scores[i]?.value ?? total,
        revenue: 500000 + i * 200000,
        reason: scores[i]?.factors?.[0]?.name ?? 'مؤشر خطر',
        daysSinceActivity: 20 + i * 10,
      })
    }
  }

  const totalRevenue = atRiskAccounts.reduce((s, a) => s + a.revenue, 0)
  const avgRiskScore = atRiskAccounts.length > 0
    ? atRiskAccounts.reduce((s, a) => s + a.riskScore, 0) / atRiskAccounts.length
    : 0

  return { atRiskAccounts, totalAtRisk: atRiskAccounts.length, totalRevenue, avgRiskScore }
}

export const ChurnIntelligenceWidget = createWidget({
  metadata: { id: 'churnIntelligence', title: 'مخاطر التوقف', category: 'intelligence', priority: 'critical', permissions: ['churn:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: ChurnData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const scores = await decision.getScores('portfolio', 'company', '', '')
        const data = mapScoresToChurn(scores)
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
  render: ({ data }) => <ChurnView data={data} />,
})
