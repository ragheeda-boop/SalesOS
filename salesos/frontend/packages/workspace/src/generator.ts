import type { UISchema, UISchemaTab, UISchemaSection, UIWidget } from '@salesos/renderer'
import type { WorkspacePreset, WorkspaceRole } from './presets'
import { getPreset } from './presets'
import type { Density } from '@salesos/design-language'

export type EntityType = 'company' | 'deal' | 'contact' | 'customer' | 'campaign' | 'revenue' | 'workspace'

export interface CapabilityDefinition {
  entityType: EntityType
  labelAr: string
  labelEn: string
  icon: string
  color: string
  widgets: string[]
  tabs: string[]
  actions?: string[]
  timeline?: boolean
  ai?: boolean
  signals?: boolean
  graph?: boolean
}

export interface WorkspaceConfig {
  entityType: EntityType
  entityId: string
  title: string
  preset: WorkspaceRole
  capability: CapabilityDefinition
  density?: Density
  customWidgets?: string[]
  hiddenTabs?: string[]
  context?: Record<string, unknown>
}

function toWidgets(ids: string[]): UIWidget[] {
  return ids.map((id) => ({
    widgetId: id,
    widgetType: id,
    title: id,
    size: 'medium',
  }))
}

export function generateWorkspace(config: WorkspaceConfig): UISchema {
  const { entityType, entityId, title, preset: presetRole, capability, context } = config
  const preset = getPreset(presetRole)
  const tabs: UISchemaTab[] = []

  const hasTimeline = capability.timeline !== false
  const hasAI = capability.ai !== false
  const hasSignals = capability.signals !== false
  const hasGraph = capability.graph !== false

  const secondaryNav: string[] = []
  if (hasTimeline) secondaryNav.push('timeline')
  if (hasAI) secondaryNav.push('ai')
  if (hasSignals) secondaryNav.push('signals')
  if (hasGraph) secondaryNav.push('graph')

  tabs.push({
    id: 'overview',
    title: 'نظرة عامة',
    sections: [
      {
        id: 'metrics-row',
        widgets: toWidgets(preset.metricWidgets || []),
      },
      {
        id: 'primary-widgets',
        widgets: toWidgets(preset.primaryWidgets || []),
      },
    ],
    widgetIds: secondaryNav.length > 0 ? secondaryNav : undefined,
  })

  for (const tabId of capability.tabs) {
    if (config.hiddenTabs?.includes(tabId)) continue
    tabs.push({
      id: tabId,
      title: tabId,
      sections: [
        {
          id: `${tabId}-content`,
          widgets: toWidgets([`${tabId}-widget`]),
        },
      ],
    })
  }

  if (hasAI && !tabs.find((t) => t.id === 'ai')) {
    tabs.push({
      id: 'ai',
      title: 'AI',
      sections: [{ id: 'ai-insights', widgets: toWidgets(['ai-insights', 'ai-recommendations']) }],
    })
  }

  return {
    schemaVersion: '5.0',
    entityType,
    entityId,
    title,
    tabs,
    context,
    actions: preset.actions?.map((a) => ({
      id: a.id,
      label: a.label,
      icon: a.icon,
      variant: a.variant || 'primary',
    })),
  }
}
