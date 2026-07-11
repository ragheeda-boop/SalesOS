export type CardStyle = 'default' | 'elevated' | 'dark' | 'bordered' | 'interactive'

export interface CardDesign {
  style: CardStyle
  borderRadius: number
  padding: number
  background: string
  shadow: string
  hoverEffect?: 'lift' | 'border' | 'glow'
}

export const CARD_DESIGNS: Record<CardStyle, CardDesign> = {
  default: { style: 'default', borderRadius: 8, padding: 16, background: '#FFFFFF', shadow: '0 1px 2px rgba(21,18,20,0.06)' },
  elevated: { style: 'elevated', borderRadius: 8, padding: 20, background: '#FFFFFF', shadow: '0 4px 6px rgba(21,18,20,0.07)', hoverEffect: 'lift' },
  dark: { style: 'dark', borderRadius: 8, padding: 20, background: '#151214', shadow: '0 4px 12px rgba(21,18,20,0.12)' },
  bordered: { style: 'bordered', borderRadius: 8, padding: 16, background: '#FFFFFF', shadow: 'none' },
  interactive: { style: 'interactive', borderRadius: 8, padding: 16, background: '#FFFFFF', shadow: '0 1px 2px rgba(21,18,20,0.06)', hoverEffect: 'border' },
} as const

export interface TableDesign {
  density: 'compact' | 'normal' | 'comfortable'
  striped: boolean
  hoverable: boolean
  stickyHeader: boolean
  rowHeight: number
  borderStyle: 'bordered' | 'horizontal' | 'borderless'
  sortable: boolean
}

export const TABLE_DESIGNS: Record<string, TableDesign> = {
  compact: { density: 'compact', striped: false, hoverable: true, stickyHeader: true, rowHeight: 40, borderStyle: 'horizontal', sortable: true },
  default: { density: 'normal', striped: true, hoverable: true, stickyHeader: true, rowHeight: 52, borderStyle: 'horizontal', sortable: true },
  comfortable: { density: 'comfortable', striped: true, hoverable: true, stickyHeader: true, rowHeight: 64, borderStyle: 'bordered', sortable: true },
} as const

import { FIXED } from './spacing'

export const SIDEBAR = {
  width: parseInt(FIXED.sidebar),
  collapsedWidth: parseInt(FIXED.sidebarCollapsed),
  background: '#151214',
  sectionGap: 24,
  itemHeight: 36,
  iconSize: 18,
  padding: 12,
} as const

export const TOPBAR = {
  height: parseInt(FIXED.topbar),
  background: '#FFFFFF',
  borderColor: '#D9D5CD',
  paddingX: 20,
} as const

export const COMMAND_BAR = {
  width: parseInt(FIXED.command),
  maxHeight: 480,
  borderRadius: 12,
} as const

export const COPILOT = {
  width: parseInt(FIXED.copilot),
  collapsedWidth: 48,
  borderRadius: 8,
} as const
