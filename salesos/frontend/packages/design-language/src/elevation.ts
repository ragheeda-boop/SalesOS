export type ElevationLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6

export type ZIndexLayer =
  | 'base'
  | 'dropdown'
  | 'sticky'
  | 'banner'
  | 'overlay'
  | 'modal'
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
}

const SHADOW_COLOR = '#151214'

export const ELEVATION: Record<ElevationLevel, ElevationStyle> = {
  0: { shadowX: 0, shadowY: 0, blur: 0, spread: 0, opacity: 0 },
  1: { shadowX: 0, shadowY: 1, blur: 2, spread: 0, opacity: 0.06 },
  2: { shadowX: 0, shadowY: 1, blur: 3, spread: 0, opacity: 0.08 },
  3: { shadowX: 0, shadowY: 4, blur: 6, spread: 0, opacity: 0.07 },
  4: { shadowX: 0, shadowY: 10, blur: 15, spread: 0, opacity: 0.08 },
  5: { shadowX: 0, shadowY: 20, blur: 25, spread: 0, opacity: 0.10 },
  6: { shadowX: 0, shadowY: 25, blur: 50, spread: 0, opacity: 0.16 },
}

export const Z_INDEX: Record<ZIndexLayer, number> = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  banner: 30,
  overlay: 40,
  modal: 50,
  toast: 60,
  'command-palette': 70,
  copilot: 80,
  max: 9999,
}

export function shadowCSS(level: ElevationLevel): string {
  const e = ELEVATION[level]
  return `0 ${e.shadowY}px ${e.blur}px ${e.spread}px rgba(21, 18, 20, ${e.opacity})`
}
