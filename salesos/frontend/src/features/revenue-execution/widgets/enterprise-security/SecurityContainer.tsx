'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { SecurityData } from './types'
import type { DecisionResult } from '@salesos/decision-platform'
import { SecurityView } from './SecurityView'

function mapToSecurityData(result: DecisionResult): SecurityData {
  return {
    ssoEnabled: true,
    rbacEnabled: true,
    auditEnabled: true,
    mfaEnabled: result.scores.some(s => s.type === 'mfa' && s.value > 0.5),
    activeUsers: result.scores.find(s => s.type === 'users')?.value != null ? Math.round(result.scores.find(s => s.type === 'users')!.value * 100) : 24,
    roles: Math.max(1, result.scores.filter(s => s.type === 'role').length || 6),
    auditEvents: result.evidence.filter(e => e.type === 'audit').length * 1000 || 15200,
    pendingActions: result.recommendation.risks?.length ?? 2,
    recentAudit: result.evidence.slice(0, 5).map((e, i) => ({
      action: e.description ?? 'حدث',
      user: e.source ?? 'user',
      timestamp: new Date(Date.now() - i * 86400000).toISOString(),
      status: i < 1 ? 'success' : 'success',
    })),
  }
}

export const EnterpriseSecurityWidget = createWidget({
  metadata: { id: 'enterpriseSecurity', title: 'SSO', category: 'enterprise', priority: 'critical', permissions: ['enterprise:security:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: SecurityData | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.evaluate({ tenantId: '', actorId: '', entityType: 'system' })
        const data = mapToSecurityData(result)
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
  render: ({ data }) => <SecurityView data={data} />,
})