import type { ComponentType } from 'react'
import type { WorkspaceWidgetEntry } from './types'

export interface RegistryEntry {
  id: string
  config: WorkspaceWidgetEntry['config']
  Container: ComponentType
}

type WidgetConfigMap = Record<string, WorkspaceWidgetEntry['config']>

export function createRegistry(
  entries: { id: string; Container: ComponentType }[],
  widgetConfig: WidgetConfigMap,
): RegistryEntry[] {
  return entries.map((entry) => ({
    ...entry,
    config: widgetConfig[entry.id] ?? {
      gridColumn: 'span 3',
      minHeight: '200px',
      refreshIntervalMs: 60000,
      staleThresholdMs: 120000,
    },
  }))
}
