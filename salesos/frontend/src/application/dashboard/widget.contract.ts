export type WidgetStatus = 'ready' | 'loading' | 'degraded' | 'error'

export interface WidgetAction {
  id: string
  label: string
  type: 'refresh' | 'navigate' | 'dismiss' | 'custom'
  payload?: Record<string, unknown>
}

export interface DashboardWidget<T> {
  id: string
  title: string
  status: WidgetStatus
  lastUpdated: string | null
  data: T | null
  actions: WidgetAction[]
}
