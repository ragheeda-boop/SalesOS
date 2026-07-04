import { useEffect } from 'react'
import { useRuntime } from './use-runtime'

export function useRealtime(channel: string, event: string, callback: (data: unknown) => void) {
  const runtime = useRuntime()

  useEffect(() => {
    const sub = runtime.realtime.subscribe(channel, event, callback)
    return () => sub.unsubscribe()
  }, [channel, event, callback, runtime])
}

export function useRealtimeStatus() {
  const runtime = useRuntime()
  return runtime.realtime.getStatus()
}
