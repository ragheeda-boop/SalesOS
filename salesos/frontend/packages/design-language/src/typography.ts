export type TextVariant = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body' | 'body-sm' | 'caption' | 'label' | 'code' | 'kbd'

export type FontWeight = 400 | 500 | 600 | 700

export interface TypographyStyle {
  size: number
  lineHeight: number
  weight: FontWeight
  letterSpacing?: number
}

export const TYPOGRAPHY: Record<TextVariant, TypographyStyle> = {
  h1: { size: 32, lineHeight: 1.15, weight: 700 },
  h2: { size: 24, lineHeight: 1.2, weight: 600 },
  h3: { size: 20, lineHeight: 1.3, weight: 600 },
  h4: { size: 18, lineHeight: 1.35, weight: 600 },
  h5: { size: 16, lineHeight: 1.4, weight: 600 },
  h6: { size: 14, lineHeight: 1.4, weight: 600 },
  body: { size: 14, lineHeight: 1.6, weight: 400 },
  'body-sm': { size: 13, lineHeight: 1.5, weight: 400 },
  caption: { size: 12, lineHeight: 1.4, weight: 400, letterSpacing: 0.2 },
  label: { size: 12, lineHeight: 1.3, weight: 500, letterSpacing: 0.3 },
  code: { size: 13, lineHeight: 1.6, weight: 400 },
  kbd: { size: 11, lineHeight: 1.3, weight: 500 },
}

export const FONT_FAMILY = {
  display: "'Viga', 'IBM Plex Sans Arabic', sans-serif",
  arabic: "'IBM Plex Sans Arabic', sans-serif",
  english: "'IBM Plex Sans', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'IBM Plex Mono', 'SF Mono', monospace",
} as const

export function typeClass(variant: TextVariant, _isRTL: boolean): string {
  const t = TYPOGRAPHY[variant]
  return `text-[${t.size}px] leading-[${t.lineHeight}] font-[${t.weight}]`
}
