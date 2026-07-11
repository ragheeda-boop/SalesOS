export type SemanticColor =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'ai'
  | 'search'
  | 'command'
  | 'workspace'
  | 'object'
  | 'timeline'
  | 'signal'
  | 'revenue'
  | 'copilot'
  | 'link'
  | 'brand'

export interface ColorPalette {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
}

export const MUHIDE = {
  orange: '#F57C1E',
  ink: '#151214',
  espresso: '#403D38',
  sand: '#CCC6BA',
  paper: '#FAFAFA',
} as const

export const COLORS: Record<SemanticColor, ColorPalette> = {
  primary: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
  secondary: {
    50: '#F7F6F4', 100: '#EDEBE6', 200: '#D9D5CD', 300: '#BFB9AD',
    400: '#A59E90', 500: '#8B8475', 600: '#706A5D', 700: '#565147',
    800: '#3D3932', 900: '#26231E',
  },
  success: {
    50: '#E8F5E9', 100: '#C8E6C9', 200: '#A5D6A7', 300: '#81C784',
    400: '#66BB6A', 500: '#4CAF50', 600: '#388E3C', 700: '#2E7D32',
    800: '#1B5E20', 900: '#0D3B0F',
  },
  warning: {
    50: '#FFF8E1', 100: '#FFECB3', 200: '#FFE082', 300: '#FFD54F',
    400: '#FFCA28', 500: '#FFC107', 600: '#FFB300', 700: '#FFA000',
    800: '#FF8F00', 900: '#E65100',
  },
  danger: {
    50: '#FFEBEE', 100: '#FFCDD2', 200: '#EF9A9A', 300: '#E57373',
    400: '#EF5350', 500: '#F44336', 600: '#E53935', 700: '#D32F2F',
    800: '#C62828', 900: '#B71C1C',
  },
  info: {
    50: '#E3F2FD', 100: '#BBDEFB', 200: '#90CAF9', 300: '#64B5F6',
    400: '#42A5F5', 500: '#2196F3', 600: '#1E88E5', 700: '#1976D2',
    800: '#1565C0', 900: '#0D47A1',
  },
  neutral: {
    50: '#F7F6F4', 100: '#EDEBE6', 200: '#D9D5CD', 300: '#BFB9AD',
    400: '#A59E90', 500: '#8B8475', 600: '#706A5D', 700: '#565147',
    800: '#3D3932', 900: '#26231E',
  },
  ai: {
    50: '#F5F3FF', 100: '#EDE9FE', 200: '#DDD6FE', 300: '#C4B5FD',
    400: '#A78BFA', 500: '#8B5CF6', 600: '#7C3AED', 700: '#6D28D9',
    800: '#5B21B6', 900: '#4C1D95',
  },
  search: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
  command: {
    50: '#F7F6F4', 100: '#EDEBE6', 200: '#D9D5CD', 300: '#BFB9AD',
    400: '#A59E90', 500: '#8B8475', 600: '#706A5D', 700: '#565147',
    800: '#3D3932', 900: '#26231E',
  },
  workspace: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
  object: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
  timeline: {
    50: '#E3F2FD', 100: '#BBDEFB', 200: '#90CAF9', 300: '#64B5F6',
    400: '#42A5F5', 500: '#2196F3', 600: '#1E88E5', 700: '#1976D2',
    800: '#1565C0', 900: '#0D47A1',
  },
  signal: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
  revenue: {
    50: '#E8F5E9', 100: '#C8E6C9', 200: '#A5D6A7', 300: '#81C784',
    400: '#66BB6A', 500: '#4CAF50', 600: '#388E3C', 700: '#2E7D32',
    800: '#1B5E20', 900: '#0D3B0F',
  },
  copilot: {
    50: '#F5F3FF', 100: '#EDE9FE', 200: '#DDD6FE', 300: '#C4B5FD',
    400: '#A78BFA', 500: '#8B5CF6', 600: '#7C3AED', 700: '#6D28D9',
    800: '#5B21B6', 900: '#4C1D95',
  },
  link: {
    50: '#E3F2FD', 100: '#BBDEFB', 200: '#90CAF9', 300: '#64B5F6',
    400: '#42A5F5', 500: '#2196F3', 600: '#1E88E5', 700: '#1976D2',
    800: '#1565C0', 900: '#0D47A1',
  },
  brand: {
    50: '#FFF3E6', 100: '#FFE2BF', 200: '#FFCE99', 300: '#FFB870',
    400: '#FFA04A', 500: '#F57C1E', 600: '#D4660F', 700: '#B35009',
    800: '#8F3C06', 900: '#6E2A03',
  },
}

export const SEMANTIC_MAP = {
  ai: { background: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800' },
  search: { background: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  command: { background: 'bg-neutral-50', text: 'text-neutral-700', border: 'border-neutral-200', badge: 'bg-neutral-100 text-neutral-800' },
  workspace: { background: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  object: { background: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  timeline: { background: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800' },
  signal: { background: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  revenue: { background: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'bg-green-100 text-green-800' },
  copilot: { background: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800' },
  link: { background: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  primary: { background: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  success: { background: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'bg-green-100 text-green-800' },
  warning: { background: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-800' },
  danger: { background: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', badge: 'bg-red-100 text-red-800' },
} as const
