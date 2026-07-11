'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { WorkspaceData } from './types'
import type { DecisionHistoryItem } from '@salesos/decision-platform'
import { MultiWorkspaceView } from './MultiWorkspaceView'

function mapHistoryToWorkspaces(history: DecisionHistoryItem[]): WorkspaceData {
  const workspaces = history.slice(0, 5).map((h, i) => ({
    id: `ws-${i}`,
    name: h.context?.entityId ?? `مساحة ${i + 1}`,
    type: h.context?.entityType ?? 'dashboard',
    active: i === 0,
    lastAccessed: h.timestamp?.split('T')[0] ?? new Date().toISOString().split('T')[0],
  }))

  if (workspaces.length === 0) {
    workspaces.push(
      { id: 'ws-default', name: 'لوحة القيادة', type: 'dashboard', active: true, lastAccessed: new Date().toISOString().split('T')[0] },
    )
  }

  return { workspaces, total: workspaces.length, active: workspaces.filter(w => w.active).length }
}

export const MultiWorkspaceWidget = createWidget({
  metadata: { id: 'multiWorkspace', title: 'مساحات العمل', category: 'enterprise', priority: 'high', permissions: ['workspace:read'], featureFlag: { enabled: true }, minHeight: '320px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: WorkspaceData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const history = await decision.getHistory('', 5)
        const data = mapHistoryToWorkspaces(history)
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
  render: ({ data }) => <MultiWorkspaceView data={data} />,
})
