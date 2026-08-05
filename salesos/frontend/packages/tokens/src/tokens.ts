/**
 * SalesOS Design Tokens — Single Source of Truth
 *
 * These tokens are consumed by:
 * - Tailwind config (via tailwind-preset.ts)
 * - CSS variables (via tokens.css)
 * - TypeScript components (via this file)
 *
 * DO NOT hardcode values in components. Always import from @salesos/tokens.
 */

// ─── Brand Colors ───────────────────────────────────────────────

export const brand = {
  orange: '#F57C1E',
  ink: '#151214',
  espresso: '#403D38',
  sand: '#CCC6BA',
  paper: '#FAFAFA',
} as const

// ─── Color Scales ───────────────────────────────────────────────

export const orange = {
  50: '#FFF3E6',
  100: '#FFE2BF',
  200: '#FFCE99',
  300: '#FFB870',
  400: '#FFA04A',
  500: '#F57C1E',
  600: '#D4660F',
  700: '#B35009',
  800: '#8F3C06',
  900: '#6E2A03',
} as const

export const neutral = {
  50: '#F7F6F4',
  100: '#EDEBE6',
  200: '#D9D5CD',
  300: '#BFB9AD',
  400: '#A59E90',
  500: '#8B8475',
  600: '#706A5D',
  700: '#565147',
  800: '#3D3932',
  900: '#26231E',
} as const

export const success = {
  50: '#E8F5E9',
  100: '#C8E6C9',
  200: '#A5D6A7',
  300: '#81C784',
  400: '#66BB6A',
  500: '#4CAF50',
  600: '#388E3C',
  700: '#2E7D32',
  800: '#1B5E20',
  900: '#0D3B0F',
} as const

export const warning = {
  50: '#FFF8E1',
  100: '#FFECB3',
  200: '#FFE082',
  300: '#FFD54F',
  400: '#FFCA28',
  500: '#FFC107',
  600: '#FFB300',
  700: '#FFA000',
  800: '#FF8F00',
  900: '#E65100',
} as const

export const danger = {
  50: '#FFEBEE',
  100: '#FFCDD2',
  200: '#EF9A9A',
  300: '#E57373',
  400: '#EF5350',
  500: '#F44336',
  600: '#E53935',
  700: '#D32F2F',
  800: '#C62828',
  900: '#B71C1C',
} as const

export const info = {
  50: '#E3F2FD',
  100: '#BBDEFB',
  200: '#90CAF9',
  300: '#64B5F6',
  400: '#42A5F5',
  500: '#2196F3',
  600: '#1E88E5',
  700: '#1976D2',
  800: '#1565C0',
  900: '#0D47A1',
} as const

// ─── Semantic Colors (Light Mode) ───────────────────────────────

export const semanticLight = {
  text: {
    primary: neutral[900],
    secondary: neutral[600],
    muted: '#8C8374',
    disabled: neutral[300],
  },
  bg: {
    primary: '#FFFFFF',
    secondary: neutral[50],
    tertiary: neutral[100],
    hover: neutral[100],
    active: neutral[200],
  },
  border: {
    default: neutral[200],
    hover: neutral[300],
    active: brand.orange,
    disabled: neutral[100],
    subtle: neutral[200],
    muted: neutral[100],
    strong: neutral[600],
  },
  surface: {
    default: '#FFFFFF',
    dark: brand.ink,
    glass: 'rgba(255, 255, 255, 0.8)',
  },
} as const

// ─── Semantic Colors (Dark Mode) ────────────────────────────────

export const semanticDark = {
  text: {
    primary: neutral[100],
    secondary: neutral[500],
    muted: neutral[700],
    disabled: neutral[700],
  },
  bg: {
    primary: brand.ink,
    secondary: neutral[900],
    tertiary: neutral[800],
    hover: '#26211E',
    active: '#3D3630',
  },
  border: {
    default: neutral[800],
    hover: neutral[700],
    active: brand.orange,
    disabled: neutral[900],
    subtle: neutral[800],
    muted: neutral[900],
    strong: neutral[500],
  },
  surface: {
    default: brand.ink,
    dark: neutral[900],
    glass: 'rgba(21, 18, 20, 0.8)',
  },
} as const

// ─── Status Colors ──────────────────────────────────────────────

export const status = {
  success: {
    text: success[700],
    bg: success[50],
    border: success[200],
    textDark: success[300],
    bgDark: success[800],
    borderDark: success[600],
  },
  danger: {
    text: danger[700],
    bg: danger[50],
    border: danger[200],
    textDark: danger[200],
    bgDark: danger[900],
    borderDark: danger[700],
  },
  warning: {
    text: '#F57F17',
    bg: warning[50],
    border: warning[200],
    textDark: warning[300],
    bgDark: warning[700],
    borderDark: warning[500],
  },
  info: {
    text: info[800],
    bg: info[50],
    border: info[200],
    textDark: info[200],
    bgDark: info[900],
    borderDark: info[700],
  },
} as const

// ─── Chart Colors ───────────────────────────────────────────────

export const chart = {
  1: brand.orange,
  2: '#22C55E',
  3: '#3B82F6',
  4: '#8B5CF6',
  5: '#F59E0B',
  6: '#EF4444',
  7: '#10B981',
  8: '#A855F7',
  9: '#06B6D4',
  10: '#EC4899',
  11: '#84CC16',
  12: '#F97316',
} as const

// ─── Typography ─────────────────────────────────────────────────

export const fontFamily = {
  display: ['Viga', 'IBM Plex Sans Arabic', 'sans-serif'],
  sans: ['IBM Plex Sans', 'sans-serif'],
  arabic: ['IBM Plex Sans Arabic', 'sans-serif'],
  mono: ['IBM Plex Mono', 'monospace'],
} as const

export const fontSize = {
  xs: ['11px', { lineHeight: '1.4' }],
  sm: ['12px', { lineHeight: '1.4' }],
  base: ['14px', { lineHeight: '1.6' }],
  lg: ['16px', { lineHeight: '1.5' }],
  xl: ['18px', { lineHeight: '1.35' }],
  '2xl': ['20px', { lineHeight: '1.3' }],
  '3xl': ['24px', { lineHeight: '1.2' }],
  '4xl': ['32px', { lineHeight: '1.15' }],
} as const

export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const

// ─── Spacing ────────────────────────────────────────────────────

export const space = {
  0: '0px',
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  2.5: '10px',
  3: '12px',
  3.5: '14px',
  4: '16px',
  5: '20px',
  6: '24px',
  7: '28px',
  8: '32px',
  9: '36px',
  10: '40px',
  12: '48px',
  14: '56px',
  16: '64px',
  20: '80px',
  24: '96px',
  28: '112px',
  32: '128px',
} as const

export const layout = {
  sidebar: '256px',
  sidebarCollapsed: '64px',
  topbar: '56px',
  copilot: '384px',
  command: '576px',
} as const

// ─── Border Radius ──────────────────────────────────────────────

export const radius = {
  sm: '2px',
  md: '6px',
  lg: '8px',
  xl: '12px',
  '2xl': '16px',
  full: '9999px',
} as const

// ─── Shadows ────────────────────────────────────────────────────

export const shadow = {
  muhide1: '0 1px 2px rgba(21,18,20,0.06)',
  muhide2: '0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)',
  muhide3: '0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)',
  muhide4: '0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)',
  muhide5: '0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)',
  muhide6: '0 25px 50px rgba(21,18,20,0.16)',
  card: '0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)',
  cardDark: '0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.15)',
} as const

// ─── Z-Index ────────────────────────────────────────────────────

export const zIndex = {
  dropdown: 10,
  sticky: 20,
  banner: 30,
  overlay: 40,
  modal: 50,
  toast: 60,
} as const

// ─── Motion ─────────────────────────────────────────────────────

export const motion = {
  duration: {
    fast: '120ms',
    normal: '200ms',
    slow: '300ms',
    slower: '400ms',
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0, 0, 1)',
    enter: 'cubic-bezier(0, 0, 0.2, 1)',
    exit: 'cubic-bezier(0.4, 0, 1, 1)',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
} as const

// ─── Focus ──────────────────────────────────────────────────────

export const focus = {
  ring: {
    color: '#2196F3',
    colorDark: '#64B5F6',
    width: '2px',
    offset: '2px',
    radius: '2px',
  },
} as const

// ─── All Tokens ─────────────────────────────────────────────────

export const tokens = {
  brand,
  orange,
  neutral,
  success,
  warning,
  danger,
  info,
  semanticLight,
  semanticDark,
  status,
  chart,
  fontFamily,
  fontSize,
  fontWeight,
  space,
  layout,
  radius,
  shadow,
  zIndex,
  motion,
  focus,
} as const

export type Tokens = typeof tokens
