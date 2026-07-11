'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { EmailSummary } from '@/application/revenue-execution/email.dto'
import type { DecisionResult } from '@salesos/decision-platform'
import { EmailView } from './EmailView'

function mapToEmails(result: DecisionResult): EmailSummary[] {
  return result.evidence.map((e, i) => ({
    threadId: `email-${i}`,
    subject: e.description?.split('.')[0] ?? `البريد ${i + 1}`,
    summary: e.description ?? '',
    sender: e.source ?? 'المرسل',
    date: new Date().toISOString().split('T')[0],
    priority: (i === 0 ? 'high' : i === 1 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
    ...(i === 0 ? { suggestedReply: result.recommendation.actionLabel } : {}),
    actionItems: [result.recommendation.actionLabel],
  }))
}

export const EmailIntelligenceWidget = createWidget({
  metadata: { id: 'emailIntelligence', title: 'ذكاء البريد', category: 'intelligence', priority: 'high', permissions: ['email:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: EmailSummary[] | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.evaluate({ tenantId: '', actorId: '', entityType: 'opportunity' })
        const data = mapToEmails(result)
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
  render: ({ data }) => <EmailView emails={data} />,
})
