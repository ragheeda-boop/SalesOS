import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'
import type { Collaborator, CursorPosition } from '@salesos/runtime'

export function useCollaboration(entityType: string, entityId: string) {
  const runtime = useRuntime()
  const session = runtime.collaboration.getSession(entityType, entityId)
  const [users, setUsers] = useState<Collaborator[]>(session?.users || [])
  const [cursors, setCursors] = useState<Map<string, CursorPosition>>(session?.cursors || new Map())

  useEffect(() => {
    const key = `${entityType}:${entityId}`
    const unsub = runtime.collaboration.subscribe(key, {
      onPresenceChange: (u) => setUsers([...u]),
      onCursorMove: () => {
        const s = runtime.collaboration.getSession(entityType, entityId)
        if (s) setCursors(new Map(s.cursors))
      },
    })
    return unsub
  }, [entityType, entityId, runtime])

  return {
    users,
    cursors,
    join: (user: { userId: string; name: string; avatar?: string }) =>
      runtime.collaboration.joinSession(entityType, entityId, user),
    leave: () => runtime.collaboration.leaveSession(entityType, entityId),
    updateCursor: (pos: Partial<CursorPosition>) =>
      runtime.collaboration.updateCursor(entityType, entityId, pos),
  }
}
