export type SpacingKey = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20 | 24 | 32 | 40 | 48 | 64

export type Density = 'compact' | 'normal' | 'comfortable' | 'spacious'

export interface DensityScale {
  row: number
  card: number
  section: number
  page: number
  table: number
  form: number
  gutter: number
}

export const SPACING: Record<SpacingKey, string> = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
  20: '80px',
  24: '96px',
  32: '128px',
  40: '160px',
  48: '192px',
  64: '256px',
}

export const DENSITY: Record<Density, DensityScale> = {
  compact: {
    row: 4, card: 6, section: 12, page: 16, table: 4, form: 6, gutter: 6,
  },
  normal: {
    row: 6, card: 12, section: 20, page: 24, table: 6, form: 12, gutter: 12,
  },
  comfortable: {
    row: 10, card: 20, section: 32, page: 40, table: 10, form: 20, gutter: 20,
  },
  spacious: {
    row: 16, card: 32, section: 48, page: 64, table: 16, form: 32, gutter: 32,
  },
} as const

export const FIXED = {
  sidebar: '256px',
  sidebarCollapsed: '64px',
  topbar: '56px',
  copilot: '384px',
  command: '576px',
  modalSm: '400px',
  modalMd: '560px',
  modalLg: '720px',
} as const
