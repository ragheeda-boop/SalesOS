export type ElevationLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12 | 16 | 24

export type ZIndexLayer =
  | 'base'
  | 'dropdown'
  | 'sticky'
  | 'navbar'
  | 'sidebar'
  | 'overlay'
  | 'modal'
  | 'tooltip'
  | 'toast'
  | 'command-palette'
  | 'copilot'
  | 'max'

export interface ElevationStyle {
  shadowX: number
  shadowY: number
  blur: number
  spread: number
  opacity: number
  darkOpacity: number
}

export const ELEVATION: Record<ElevationLevel, ElevationStyle> = {
  0: { shadowX: 0, shadowY: 0, blur: 0, spread: 0, opacity: 0, darkOpacity: 0 },
  1: { shadowX: 0, shadowY: 1, blur: 2, spread: 0, opacity: 0.05, darkOpacity: 0.2 },
  2: { shadowX: 0, shadowY: 1, blur: 3, spread: 0, opacity: 0.1, darkOpacity: 0.25 },
  3: { shadowX: 0, shadowY: 2, blur: 4, spread: -1, opacity: 0.1, darkOpacity: 0.3 },
  4: { shadowX: 0, shadowY: 4, blur: 6, spread: -2, opacity: 0.1, darkOpacity: 0.35 },
  5: { shadowX: 0, shadowY: 4, blur: 8, spread: -2, opacity: 0.12, darkOpacity: 0.4 },
  6: { shadowX: 0, shadowY: 6, blur: 12, spread: -2, opacity: 0.15, darkOpacity: 0.45 },
  8: { shadowX: 0, shadowY: 8, blur: 16, spread: -4, opacity: 0.15, darkOpacity: 0.5 },
  12: { shadowX: 0, shadowY: 12, blur: 24, spread: -4, opacity: 0.2, darkOpacity: 0.55 },
  16: { shadowX: 0, shadowY: 16, blur: 32, spread: -8, opacity: 0.2, darkOpacity: 0.6 },
  24: { shadowX: 0, shadowY: 24, blur: 48, spread: -12, opacity: 0.25, darkOpacity: 0.65 },
}

export const Z_INDEX: Record<ZIndexLayer, number> = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  navbar: 1030,
  sidebar: 1040,
  overlay: 1050,
  modal: 1060,
  tooltip: 1070,
  toast: 1080,
  'command-palette': 1090,
  copilot: 1100,
  max: 9999,
}

export function shadowCSS(level: ElevationLevel, dark: boolean): string {
  const e = ELEVATION[level]
  const opacity = dark ? e.darkOpacity : e.opacity
  return `0 ${e.shadowY}px ${e.blur}px ${e.spread}px rgba(0,0,0,${opacity})`
}
