'use client'

import { useCallback } from 'react'
import { useDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import type { AICoachAction } from '@/lib/api'
import { AICoachView } from './AICoachView'

export function AICoachContainer({ actions }: { actions: AICoachAction[] }) {
  const decision = useDecision()

  const handleActionClick = useCallback(async (action: AICoachAction) => {
    try {
      await decision.evaluate({
        tenantId: '',
        actorId: '',
        entityType: 'opportunity',
        metadata: { coachAction: action.type, title: action.title },
      })
    } catch {
      // silently ignore decision platform errors
    }
  }, [decision])

  return <AICoachView actions={actions} onActionClick={handleActionClick} />
}
