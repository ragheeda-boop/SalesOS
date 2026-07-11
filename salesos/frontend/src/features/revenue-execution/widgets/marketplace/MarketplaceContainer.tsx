'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { PluginData } from './types'
import type { DecisionResult } from '@salesos/decision-platform'
import { MarketplaceView } from './MarketplaceView'

function mapToPluginData(result: DecisionResult): PluginData {
  const apps = result.evidence.map((e, i) => ({
    id: `plugin-${i}`,
    name: e.description?.split(':')[0] ?? `التطبيق ${i + 1}`,
    description: e.description ?? '',
    installed: i === 0,
    version: '1.0.0',
    icon: ['chart', 'message', 'database', 'cloud', 'lock'][i % 5],
    category: result.recommendation.actionLabel ?? 'عام',
  }))
  return {
    plugins: apps,
    installed: apps.filter(a => a.installed).length,
    available: apps.length,
  }
}

export const MarketplaceWidget = createWidget({
  metadata: { id: 'marketplace', title: 'المتجر', category: 'enterprise', priority: 'medium', permissions: ['enterprise:marketplace:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: PluginData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.evaluate({ tenantId: '', actorId: '', entityType: 'app' })
        const data = mapToPluginData(result)
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
  render: ({ data }) => <MarketplaceView data={data} />,
})
