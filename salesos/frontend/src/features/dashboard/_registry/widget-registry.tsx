import type { ComponentType } from 'react'
import type { DashboardWidget } from '@/application/dashboard/widget.contract'
import type { WidgetId, WidgetConfig } from './widget-config'
import { getWidgetConfig } from './widget-config'

export interface RegistryEntry {
  id: WidgetId
  config: WidgetConfig
  Container: ComponentType
}

export function createRegistry(
  entries: { id: WidgetId; Container: ComponentType }[]
): RegistryEntry[] {
  return entries.map((entry) => ({
    ...entry,
    config: getWidgetConfig(entry.id),
  }))
}
