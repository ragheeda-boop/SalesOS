export type TextVariant = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body' | 'body-sm' | 'caption' | 'label' | 'code' | 'kbd'

export type FontWeight = 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900

export interface TypographyStyle {
  size: number
  lineHeight: number
  weight: FontWeight
  letterSpacing?: number
  arabicSize?: number
}

export const TYPOGRAPHY: Record<TextVariant, TypographyStyle> = {
  h1: { size: 32, lineHeight: 1.3, weight: 700, arabicSize: 30 },
  h2: { size: 24, lineHeight: 1.35, weight: 600, arabicSize: 22 },
  h3: { size: 20, lineHeight: 1.4, weight: 600, arabicSize: 18 },
  h4: { size: 18, lineHeight: 1.45, weight: 600, arabicSize: 16 },
  h5: { size: 16, lineHeight: 1.5, weight: 600, arabicSize: 15 },
  h6: { size: 14, lineHeight: 1.5, weight: 600, arabicSize: 13 },
  body: { size: 14, lineHeight: 1.6, weight: 400 },
  'body-sm': { size: 13, lineHeight: 1.5, weight: 400 },
  caption: { size: 12, lineHeight: 1.4, weight: 400, letterSpacing: 0.2 },
  label: { size: 12, lineHeight: 1.3, weight: 500, letterSpacing: 0.3 },
  code: { size: 13, lineHeight: 1.6, weight: 400 },
  kbd: { size: 11, lineHeight: 1.3, weight: 500 },
}

export const FONT_FAMILY = {
  arabic: "'Noto Sans Arabic', 'Tajawal', 'Cairo', sans-serif",
  english: "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
  numbers: "'Inter', 'SF Pro Display', sans-serif",
} as const

export function typeClass(variant: TextVariant, isRTL: boolean): string {
  const t = TYPOGRAPHY[variant]
  const size = isRTL && t.arabicSize ? t.arabicSize : t.size
  return `text-[${size}px] leading-[${t.lineHeight}] font-[${t.weight}]`
}
