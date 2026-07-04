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
  950: string
}

export const COLORS: Record<SemanticColor, ColorPalette> = {
  primary: {
    50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
    400: '#60A5FA', 500: '#3B82F6', 600: '#2563EB', 700: '#1D4ED8',
    800: '#1E40AF', 900: '#1E3A8A', 950: '#172554',
  },
  secondary: {
    50: '#F8FAFC', 100: '#F1F5F9', 200: '#E2E8F0', 300: '#CBD5E1',
    400: '#94A3B8', 500: '#64748B', 600: '#475569', 700: '#334155',
    800: '#1E293B', 900: '#0F172A', 950: '#020617',
  },
  success: {
    50: '#F0FDF4', 100: '#DCFCE7', 200: '#BBF7D0', 300: '#86EFAC',
    400: '#4ADE80', 500: '#22C55E', 600: '#16A34A', 700: '#15803D',
    800: '#166534', 900: '#14532D', 950: '#052E16',
  },
  warning: {
    50: '#FFFBEB', 100: '#FEF3C7', 200: '#FDE68A', 300: '#FCD34D',
    400: '#FBBF24', 500: '#F59E0B', 600: '#D97706', 700: '#B45309',
    800: '#92400E', 900: '#78350F', 950: '#451A03',
  },
  danger: {
    50: '#FEF2F2', 100: '#FEE2E2', 200: '#FECACA', 300: '#FCA5A5',
    400: '#F87171', 500: '#EF4444', 600: '#DC2626', 700: '#B91C1C',
    800: '#991B1B', 900: '#7F1D1D', 950: '#450A0A',
  },
  info: {
    50: '#ECFEFF', 100: '#CFFAFE', 200: '#A5F3FC', 300: '#67E8F9',
    400: '#22D3EE', 500: '#06B6D4', 600: '#0891B2', 700: '#0E7490',
    800: '#155E75', 900: '#164E63', 950: '#083344',
  },
  neutral: {
    50: '#F9FAFB', 100: '#F3F4F6', 200: '#E5E7EB', 300: '#D1D5DB',
    400: '#9CA3AF', 500: '#6B7280', 600: '#4B5563', 700: '#374151',
    800: '#1F2937', 900: '#111827', 950: '#030712',
  },
  ai: {
    50: '#F5F3FF', 100: '#EDE9FE', 200: '#DDD6FE', 300: '#C4B5FD',
    400: '#A78BFA', 500: '#8B5CF6', 600: '#7C3AED', 700: '#6D28D9',
    800: '#5B21B6', 900: '#4C1D95', 950: '#2E1065',
  },
  search: {
    50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
    400: '#60A5FA', 500: '#3B82F6', 600: '#2563EB', 700: '#1D4ED8',
    800: '#1E40AF', 900: '#1E3A8A', 950: '#172554',
  },
  command: {
    50: '#F0F9FF', 100: '#E0F2FE', 200: '#BAE6FD', 300: '#7DD3FC',
    400: '#38BDF8', 500: '#0EA5E9', 600: '#0284C7', 700: '#0369A1',
    800: '#075985', 900: '#0C4A6E', 950: '#082F49',
  },
  workspace: {
    50: '#F0FDF4', 100: '#DCFCE7', 200: '#BBF7D0', 300: '#86EFAC',
    400: '#4ADE80', 500: '#22C55E', 600: '#16A34A', 700: '#15803D',
    800: '#166534', 900: '#14532D', 950: '#052E16',
  },
  object: {
    50: '#FFF7ED', 100: '#FFEDD5', 200: '#FED7AA', 300: '#FDBA74',
    400: '#FB923C', 500: '#F97316', 600: '#EA580C', 700: '#C2410C',
    800: '#9A3412', 900: '#7C2D12', 950: '#431407',
  },
  timeline: {
    50: '#F0F9FF', 100: '#E0F2FE', 200: '#BAE6FD', 300: '#7DD3FC',
    400: '#38BDF8', 500: '#0EA5E9', 600: '#0284C7', 700: '#0369A1',
    800: '#075985', 900: '#0C4A6E', 950: '#082F49',
  },
  signal: {
    50: '#FFF7ED', 100: '#FFEDD5', 200: '#FED7AA', 300: '#FDBA74',
    400: '#FB923C', 500: '#F97316', 600: '#EA580C', 700: '#C2410C',
    800: '#9A3412', 900: '#7C2D12', 950: '#431407',
  },
  revenue: {
    50: '#F0FDF4', 100: '#DCFCE7', 200: '#BBF7D0', 300: '#86EFAC',
    400: '#4ADE80', 500: '#22C55E', 600: '#16A34A', 700: '#15803D',
    800: '#166534', 900: '#14532D', 950: '#052E16',
  },
  copilot: {
    50: '#F5F3FF', 100: '#EDE9FE', 200: '#DDD6FE', 300: '#C4B5FD',
    400: '#A78BFA', 500: '#8B5CF6', 600: '#7C3AED', 700: '#6D28D9',
    800: '#5B21B6', 900: '#4C1D95', 950: '#2E1065',
  },
  link: {
    50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
    400: '#60A5FA', 500: '#3B82F6', 600: '#2563EB', 700: '#1D4ED8',
    800: '#1E40AF', 900: '#1E3A8A', 950: '#172554',
  },
  brand: {
    50: '#EEF2FF', 100: '#E0E7FF', 200: '#C7D2FE', 300: '#A5B4FC',
    400: '#818CF8', 500: '#6366F1', 600: '#4F46E5', 700: '#4338CA',
    800: '#3730A3', 900: '#312E81', 950: '#1E1B4B',
  },
}

export const SEMANTIC_MAP = {
  ai: { background: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800' },
  search: { background: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800' },
  command: { background: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200', badge: 'bg-sky-100 text-sky-800' },
  workspace: { background: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'bg-green-100 text-green-800' },
  object: { background: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  timeline: { background: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200', badge: 'bg-sky-100 text-sky-800' },
  signal: { background: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' },
  revenue: { background: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800' },
  copilot: { background: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800' },
  link: { background: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  primary: { background: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800' },
  success: { background: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'bg-green-100 text-green-800' },
  warning: { background: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-800' },
  danger: { background: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', badge: 'bg-red-100 text-red-800' },
} as const
