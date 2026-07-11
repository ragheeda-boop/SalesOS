'use client'

import { useState, useEffect, useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useDecision } from '../../_providers/DecisionProvider'
import type { MeetingBrief } from '@/application/revenue-execution/meeting.dto'
import type { DecisionResult } from '@salesos/decision-platform'
import { MeetingView } from './MeetingView'

function mapToMeetingBrief(result: DecisionResult): MeetingBrief {
  return {
    companyName: result.explainability?.why?.split(' ')[0] ?? 'الشركة',
    meetingTitle: result.recommendation.actionLabel,
    date: new Date().toISOString().split('T')[0],
    attendees: result.evidence.slice(0, 3).map((e, i) => ({
      name: e.source ?? `حضور ${i + 1}`,
      role: e.type === 'contact' ? 'صاحب قرار' : 'حاضر',
      influence: i === 0 ? 'عالي' : 'متوسط' as const,
    })),
    recentSignals: result.evidence.filter(e => e.type === 'signal').map(e => e.description).filter(Boolean),
    risks: result.recommendation.risks?.map(r => r.description) ?? [],
    opportunities: result.recommendation.alternatives?.map(a => a.actionLabel) ?? [],
    talkingPoints: [
      result.recommendation.reason,
      ...(result.evidence.slice(0, 2).map(e => e.description)),
    ].filter(Boolean),
    recommendedAction: result.recommendation.actionLabel,
  }
}

export const MeetingIntelligenceWidget = createWidget({
  metadata: {
    id: 'meetingIntelligence', title: 'ذكاء الاجتماعات', category: 'intelligence', priority: 'high',
    permissions: ['meeting:read'], featureFlag: { enabled: true }, minHeight: '360px',
  },
  useData: () => {
    const decision = useDecision()
    const [state, setState] = useState<{ data: MeetingBrief | null; status: 'loading' | 'ready' | 'error'; lastUpdated: string | null; error: Error | null }>({ data: null, status: 'loading', lastUpdated: null, error: null })

    const fetchData = useCallback(async () => {
      setState(prev => ({ ...prev, status: 'loading', error: null }))
      try {
        const result = await decision.evaluate({ tenantId: '', actorId: '', entityType: 'opportunity' })
        const data = mapToMeetingBrief(result)
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
  render: ({ data }) => <MeetingView brief={data} />,
})
