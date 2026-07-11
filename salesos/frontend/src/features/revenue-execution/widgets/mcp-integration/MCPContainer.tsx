'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { MCPData } from './types'
import type { DecisionResult } from '@salesos/decision-platform'
import { MCPView } from './MCPView'

function mapToMCPData(result: DecisionResult): MCPData {
  const connections = result.evidence.map((e, i) => ({
    id: `conn-${i}`,
    name: e.source ?? `اتصال ${i + 1}`,
    type: e.type === 'database' ? 'قاعدة بيانات' : e.type === 'api' ? 'API' : e.type === 'erp' ? 'ERP' : e.type ?? 'نظام',
    status: (i === 0 || i === 1 ? 'connected' : 'disconnected') as 'connected' | 'disconnected' | 'error',
    lastSync: i < 2 ? new Date().toISOString().split('T')[0] : undefined,
    entities: (i + 1) * 12500,
  }))

  return {
    connections,
    totalConnections: connections.length,
    activeConnections: connections.filter(c => c.status === 'connected').length,
    syncedEntities: connections.reduce((s, c) => s + c.entities, 0),
  }
}

export const MCPIntegrationWidget = createWidget({
  metadata: { id: 'mcpIntegration', title: 'اتصالات MCP', category: 'enterprise', priority: 'medium', permissions: ['enterprise:mcp:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: MCPData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.evaluate({ tenantId: '', actorId: '', entityType: 'system' })
        const data = mapToMCPData(result)
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
  render: ({ data }) => <MCPView data={data} />,
})
