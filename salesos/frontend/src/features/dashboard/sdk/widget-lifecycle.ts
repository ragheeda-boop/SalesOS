import { useEffect, useRef } from 'react'
import type { WidgetStatus, WidgetMetadata, WidgetLifecycle as LifecycleHooks } from './types'

export function useWidgetLifecycle(
  id: string,
  metadata: WidgetMetadata,
  status: WidgetStatus,
  hooks?: LifecycleHooks,
) {
  const prevStatus = useRef<WidgetStatus>(status)

  useEffect(() => {
    hooks?.onMount?.({ id, metadata })
    return () => hooks?.onUnmount?.({ id, metadata })
  }, [id])

  useEffect(() => {
    if (prevStatus.current !== status) {
      hooks?.onStatusChange?.({ id, metadata, status, previous: prevStatus.current })
      prevStatus.current = status
    }
  })

  return {
    notifyRefresh: () => hooks?.onRefresh?.({ id, metadata }),
    notifyError: (error: Error) => hooks?.onError?.({ id, metadata, error }),
  }
}
