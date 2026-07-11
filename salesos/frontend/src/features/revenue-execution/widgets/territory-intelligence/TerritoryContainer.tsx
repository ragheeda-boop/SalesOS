'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { TerritoryData } from './types'
import type { Score } from '@salesos/decision-platform'
import { TerritoryView } from './TerritoryView'

function mapScoresToTerritory(scores: Score[]): TerritoryData {
  const territories = scores.filter(s => s.type === 'territory').map((s, i) => ({
    id: `territory-${i}`,
    name: (s.metadata?.name as string) ?? `منطقة ${i + 1}`,
    deals: (s.metadata?.deals as number) ?? Math.round(s.value * 10),
    value: (s.metadata?.value as number) ?? Math.round(s.value * 5000000),
    quota: (s.metadata?.quota as number) ?? Math.round(s.value * 6000000),
    attainment: Math.round(s.value * 100),
  }))

  const regionScores = scores.filter(s => s.type === 'region')
  for (const s of regionScores) {
    territories.push({
      id: `territory-${territories.length}`,
      name: (s.metadata?.name as string) ?? `منطقة ${territories.length}`,
      deals: (s.metadata?.deals as number) ?? Math.round(s.value * 8),
      value: (s.metadata?.value as number) ?? Math.round(s.value * 4000000),
      quota: (s.metadata?.quota as number) ?? Math.round(s.value * 5000000),
      attainment: Math.round(s.value * 100),
    })
  }

  const coverage = territories.filter(t => t.attainment >= 50).map(t => ({
    region: t.name,
    covered: true,
    salesReps: Math.max(1, Math.round(t.deals / 3)),
    opportunityValue: t.value,
  }))

  const gaps = territories.filter(t => t.attainment < 50).map(t => ({
    region: t.name,
    potentialValue: t.quota - t.value,
    reason: t.attainment < 30 ? 'تغطية ضعيفة' : 'أداء دون المستوى',
  }))

  return { territories, coverage, gaps }
}

export const TerritoryIntelligenceWidget = createWidget({
  metadata: { id: 'territoryIntelligence', title: 'ذكاء المناطق', category: 'intelligence', priority: 'high', permissions: ['territory:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: TerritoryData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const scores = await decision.getScores('territories', 'company', '', '')
        const data = mapScoresToTerritory(scores)
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
  render: ({ data }) => <TerritoryView data={data} />,
})
