export type WorkspacePreset = 'sales' | 'marketing' | 'executive' | 'legal' | 'customer' | 'custom'

export type WorkspaceZone = 'header' | 'toolbar' | 'sidebar' | 'timeline' | 'main' | 'signals' | 'graph' | 'ai'

export interface WorkspaceLayout {
  preset: WorkspacePreset
  zones: WorkspaceZone[]
  defaultWidgets: string[]
  grid: {
    columns: number
    gap: number
    rows?: number
  }
  sidebar?: {
    width: number
    position: 'left' | 'right'
    collapsed?: boolean
  }
  timeline?: {
    position: 'sidebar' | 'bottom' | 'tab'
    collapsed?: boolean
  }
}

export const WORKSPACE_PRESETS: Record<WorkspacePreset, WorkspaceLayout> = {
  sales: {
    preset: 'sales',
    zones: ['header', 'toolbar', 'main', 'timeline', 'ai', 'signals'],
    defaultWidgets: ['overview', 'revenue', 'buying-committee', 'timeline', 'recommendations', 'tasks'],
    grid: { columns: 3, gap: 16 },
    sidebar: { width: 320, position: 'right', collapsed: false },
    timeline: { position: 'sidebar', collapsed: false },
  },
  marketing: {
    preset: 'marketing',
    zones: ['header', 'main', 'signals', 'graph', 'ai'],
    defaultWidgets: ['campaigns', 'audience', 'channels', 'content', 'analytics', 'signals'],
    grid: { columns: 3, gap: 16 },
    sidebar: { width: 320, position: 'right', collapsed: true },
  },
  executive: {
    preset: 'executive',
    zones: ['header', 'main', 'ai'],
    defaultWidgets: ['revenue-overview', 'forecast', 'health', 'recommendations', 'hot-accounts', 'signals'],
    grid: { columns: 2, gap: 20 },
    sidebar: { width: 400, position: 'right', collapsed: false },
  },
  legal: {
    preset: 'legal',
    zones: ['header', 'main', 'timeline'],
    defaultWidgets: ['documents', 'licenses', 'contracts', 'compliance', 'audit', 'tasks'],
    grid: { columns: 2, gap: 16 },
    timeline: { position: 'bottom', collapsed: false },
  },
  customer: {
    preset: 'customer',
    zones: ['header', 'main', 'timeline', 'ai'],
    defaultWidgets: ['overview', 'health', 'licenses', 'tickets', 'tasks', 'recommendations'],
    grid: { columns: 3, gap: 16 },
    sidebar: { width: 320, position: 'right', collapsed: false },
    timeline: { position: 'sidebar', collapsed: false },
  },
  custom: {
    preset: 'custom',
    zones: ['header', 'toolbar', 'main', 'timeline', 'sidebar', 'signals', 'graph', 'ai'],
    defaultWidgets: [],
    grid: { columns: 3, gap: 16 },
    sidebar: { width: 320, position: 'right', collapsed: false },
    timeline: { position: 'sidebar', collapsed: false },
  },
} as const
