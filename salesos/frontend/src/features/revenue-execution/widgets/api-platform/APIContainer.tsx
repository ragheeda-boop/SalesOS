'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { APIData } from './types'
import type { Score } from '@salesos/decision-platform'
import { APIView } from './APIView'

function mapScoresToAPI(scores: Score[]): APIData {
  const endpoints = scores.map((s, i) => ({
    method: (s.metadata?.method as string) ?? (i % 2 === 0 ? 'GET' : 'POST'),
    path: (s.metadata?.path as string) ?? '/api/v1/' + s.type,
    description: s.type ?? '',
    calls: (s.metadata?.calls as number) ?? Math.round(s.value * 50000),
    avgLatency: (s.metadata?.latency as number) ?? Math.round((1 - s.value) * 200),
  }))

  return {
    endpoints,
    totalEndpoints: endpoints.length,
    totalCalls: endpoints.reduce((sum, e) => sum + e.calls, 0),
    avgLatency: endpoints.length > 0 ? Math.round(endpoints.reduce((sum, e) => sum + e.avgLatency, 0) / endpoints.length) : 0,
    errorRate: scores.filter(s => s.type === 'error').reduce((sum, s) => sum + s.value, 0) * 10,
  }
}

export const APIPlatformWidget = createWidget({
  metadata: { id: 'apiPlatform', title: 'API', category: 'enterprise', priority: 'medium', permissions: ['enterprise:api:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: APIData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const scores = await decision.getScores('api', 'system', '', '')
        const data = mapScoresToAPI(scores)
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
  render: ({ data }) => <APIView data={data} />,
})