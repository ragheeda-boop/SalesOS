import type { WidgetStatus } from '@salesos/widget-sdk'

export interface WorkspaceWidgetEntry {
  id: string
  config: {
    gridColumn: string
    minHeight: string
    refreshIntervalMs: number
    staleThresholdMs: number
  }
}

export interface WorkspaceContextValue<W extends Record<string, unknown>> {
  widgets: W
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}
