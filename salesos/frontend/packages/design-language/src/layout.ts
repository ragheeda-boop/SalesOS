export type LayoutZone = 'header' | 'toolbar' | 'sidebar' | 'content' | 'panel' | 'timeline' | 'copilot' | 'footer'

export type LayoutPreset = 'single' | 'split' | 'sidebar-main' | 'main-panel' | 'three-column' | 'dashboard' | 'workspace' | 'fullscreen'

export type ResponsiveBreakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'

export const BREAKPOINTS: Record<ResponsiveBreakpoint, number> = {
  xs: 480,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
}

export interface ZoneConfig {
  id: LayoutZone
  minWidth?: number
  maxWidth?: number
  defaultWidth?: number
  resizable?: boolean
  collapsible?: boolean
  defaultCollapsed?: boolean
  order: number
  priority: number
}

export const WORKSPACE_ZONES: Record<LayoutZone, ZoneConfig> = {
  header: { id: 'header', order: 0, priority: 1, minWidth: 320 },
  toolbar: { id: 'toolbar', order: 1, priority: 2, minWidth: 320 },
  sidebar: { id: 'sidebar', order: 2, priority: 3, defaultWidth: 256, minWidth: 64, maxWidth: 320, resizable: true, collapsible: true },
  content: { id: 'content', order: 3, priority: 4, minWidth: 320 },
  panel: { id: 'panel', order: 4, priority: 5, defaultWidth: 384, minWidth: 320, maxWidth: 480, resizable: true, collapsible: true },
  timeline: { id: 'timeline', order: 5, priority: 6, defaultWidth: 320, minWidth: 240, maxWidth: 480, collapsible: true },
  copilot: { id: 'copilot', order: 6, priority: 7, defaultWidth: 384, minWidth: 320, maxWidth: 480, collapsible: true },
  footer: { id: 'footer', order: 7, priority: 8 },
}

export const GRID = {
  columns: 12,
  gutter: 16,
  margin: 24,
  maxWidth: 1440,
  widgetMinWidth: 240,
  widgetMaxWidth: 960,
} as const

export const SIDEBAR_WIDTH = 256
export const SIDEBAR_COLLAPSED = 64
export const TOPBAR_HEIGHT = 56

export function gridColumns(width: number): number {
  if (width < BREAKPOINTS.sm) return 4
  if (width < BREAKPOINTS.lg) return 8
  return 12
}

export function zoneVisibility(zone: LayoutZone, breakpoint: ResponsiveBreakpoint): boolean {
  if (zone === 'copilot' || zone === 'panel') return breakpoint !== 'xs' && breakpoint !== 'sm'
  if (zone === 'timeline') return breakpoint !== 'xs'
  if (zone === 'sidebar' && (breakpoint === 'xs' || breakpoint === 'sm')) return false
  return true
}
