export type SpacingScale = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20 | 24 | 32 | 40 | 48 | 64

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

export const SPACING: Record<SpacingScale, string> = {
  0: '0px',
  1: '2px',
  2: '4px',
  3: '6px',
  4: '8px',
  5: '10px',
  6: '12px',
  8: '16px',
  10: '20px',
  12: '24px',
  16: '32px',
  20: '40px',
  24: '48px',
  32: '64px',
  40: '80px',
  48: '96px',
  64: '128px',
}

export const DENSITY: Record<Density, DensityScale> = {
  compact: {
    row: 4,
    card: 6,
    section: 12,
    page: 16,
    table: 4,
    form: 6,
    gutter: 6,
  },
  normal: {
    row: 6,
    card: 12,
    section: 20,
    page: 24,
    table: 6,
    form: 12,
    gutter: 12,
  },
  comfortable: {
    row: 10,
    card: 20,
    section: 32,
    page: 40,
    table: 10,
    form: 20,
    gutter: 20,
  },
  spacious: {
    row: 16,
    card: 32,
    section: 48,
    page: 64,
    table: 16,
    form: 32,
    gutter: 32,
  },
} as const
