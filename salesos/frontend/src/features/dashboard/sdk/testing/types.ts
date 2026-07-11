import type { WidgetStatus, WidgetData, WidgetFeatureFlag } from '../types'

export interface MockWidgetContext<T> {
  data: T | null
  status: WidgetStatus
  lastUpdated: string | null
  error: Error | null
  refetch: () => void
}

export type MockFactory<T> = (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
