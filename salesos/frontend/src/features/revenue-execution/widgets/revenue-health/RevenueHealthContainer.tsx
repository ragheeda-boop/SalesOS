'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { RevenueHealthData } from './types'
import type { Score } from '@salesos/decision-platform'
import { RevenueHealthView } from './RevenueHealthView'

function mapScoresToHealth(scores: Score[]): RevenueHealthData {
  const excellent = scores.filter(s => s.value >= 0.8).length
  const good = scores.filter(s => s.value >= 0.6 && s.value < 0.8).length
  const fair = scores.filter(s => s.value >= 0.4 && s.value < 0.6).length
  const poor = scores.filter(s => s.value < 0.4).length
  const total = scores.length || 1

  return {
    totalPortfolio: scores.length,
    activeAccounts: excellent + good,
    atRisk: poor,
    growthAccounts: excellent,
    healthDistribution: [
      { label: 'ممتاز', count: excellent, value: Math.round((excellent / total) * 100), color: 'bg-green-500' },
      { label: 'جيد', count: good, value: Math.round((good / total) * 100), color: 'bg-blue-500' },
      { label: 'متوسط', count: fair, value: Math.round((fair / total) * 100), color: 'bg-amber-500' },
      { label: 'ضعيف', count: poor, value: Math.round((poor / total) * 100), color: 'bg-red-500' },
    ],
  }
}

export const RevenueHealthWidget = createWidget({
  metadata: { id: 'revenueHealth', title: 'صحة الإيرادات', category: 'intelligence', priority: 'high', permissions: ['revenue:health:read'], featureFlag: { enabled: true }, minHeight: '280px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: RevenueHealthData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const scores = await decision.getScores('portfolio', 'company', '', '')
        const data = mapScoresToHealth(scores)
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
  render: ({ data }) => <RevenueHealthView data={data} />,
})
