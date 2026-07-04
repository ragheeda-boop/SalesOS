import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'
import type { Session } from '@salesos/runtime'

export function useSession(): Session {
  const runtime = useRuntime()
  const [session, setSession] = useState<Session>(runtime.session.getSession())

  useEffect(() => {
    const unsub = runtime.session.subscribe((s) => setSession({ ...s }))
    return unsub
  }, [runtime])

  return session
}

export function useUser() {
  const session = useSession()
  return session.user
}

export function useIsAuthenticated() {
  const session = useSession()
  return session.authenticated
}
