export type CardStyle = 'default' | 'elevated' | 'borderless' | 'highlighted' | 'interactive'

export interface CardDesign {
  style: CardStyle
  borderRadius: number
  padding: number
  shadow: string
  hoverEffect?: 'lift' | 'border' | 'glow'
}

export const CARD_DESIGNS: Record<CardStyle, CardDesign> = {
  default: { style: 'default', borderRadius: 12, padding: 16, shadow: '0 1px 2px rgba(0,0,0,0.05)' },
  elevated: { style: 'elevated', borderRadius: 12, padding: 20, shadow: '0 4px 12px rgba(0,0,0,0.08)', hoverEffect: 'lift' },
  borderless: { style: 'borderless', borderRadius: 0, padding: 16, shadow: 'none' },
  highlighted: { style: 'highlighted', borderRadius: 12, padding: 20, shadow: '0 0 0 2px #3B82F6' },
  interactive: { style: 'interactive', borderRadius: 12, padding: 16, shadow: '0 1px 2px rgba(0,0,0,0.05)', hoverEffect: 'border' },
} as const

export interface TableDesign {
  density: 'compact' | 'normal' | 'comfortable'
  striped: boolean
  hoverable: boolean
  stickyHeader: boolean
  rowHeight: number
  borderStyle: 'bordered' | 'horizontal' | 'borderless'
  sortable: boolean
  selection: 'none' | 'single' | 'multi'
}

export const TABLE_DESIGNS: Record<string, TableDesign> = {
  compact: { density: 'compact', striped: false, hoverable: true, stickyHeader: true, rowHeight: 40, borderStyle: 'horizontal', sortable: true, selection: 'none' },
  default: { density: 'normal', striped: true, hoverable: true, stickyHeader: true, rowHeight: 52, borderStyle: 'horizontal', sortable: true, selection: 'single' },
  comfortable: { density: 'comfortable', striped: true, hoverable: true, stickyHeader: true, rowHeight: 64, borderStyle: 'bordered', sortable: true, selection: 'multi' },
} as const

export interface FormDesign {
  layout: 'single' | 'two-column' | 'three-column' | 'inline'
  labelPosition: 'top' | 'side' | 'floating'
  density: 'compact' | 'normal' | 'comfortable'
  showRequiredMarkers: boolean
  validationStyle: 'inline' | 'tooltip' | 'summary'
  submitBehavior: 'stay' | 'navigate' | 'close'
}

export const FORM_DESIGNS: Record<string, FormDesign> = {
  default: { layout: 'single', labelPosition: 'top', density: 'normal', showRequiredMarkers: true, validationStyle: 'inline', submitBehavior: 'stay' },
  quick: { layout: 'inline', labelPosition: 'floating', density: 'compact', showRequiredMarkers: false, validationStyle: 'tooltip', submitBehavior: 'close' },
  wizard: { layout: 'single', labelPosition: 'top', density: 'comfortable', showRequiredMarkers: true, validationStyle: 'summary', submitBehavior: 'navigate' },
} as const

export interface ChartDesign {
  showLegend: boolean
  showTooltips: boolean
  showGrid: boolean
  animate: boolean
  colors: string[]
  height: number
}

export const CHART_DESIGNS: Record<string, ChartDesign> = {
  default: { showLegend: true, showTooltips: true, showGrid: true, animate: true, colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'], height: 200 },
  compact: { showLegend: false, showTooltips: true, showGrid: false, animate: true, colors: ['#3B82F6', '#10B981', '#F59E0B'], height: 120 },
  dashboard: { showLegend: true, showTooltips: true, showGrid: true, animate: true, colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'], height: 300 },
} as const
