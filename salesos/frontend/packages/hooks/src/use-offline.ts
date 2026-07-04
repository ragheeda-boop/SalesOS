import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'

export function useOfflineStatus() {
  const runtime = useRuntime()
  const [status, setStatus] = useState(runtime.offline.getStatus())

  useEffect(() => {
    const unsub = runtime.offline.onStatusChange(setStatus)
    return unsub
  }, [runtime])

  return status
}

export function useOfflineQueue() {
  const runtime = useRuntime()
  return runtime.offline.getQueue()
}
