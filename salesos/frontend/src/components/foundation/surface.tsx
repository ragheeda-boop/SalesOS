import { cn } from "@salesos/ui"

type SurfaceVariant = 'default' | 'elevated' | 'dark' | 'bordered' | 'glass'

interface SurfaceProps {
  variant?: SurfaceVariant
  as?: React.ElementType
  padding?: 'none' | 'sm' | 'md' | 'lg'
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  children: React.ReactNode
  className?: string
}

const VARIANT_MAP: Record<SurfaceVariant, string> = {
  default: 'bg-[var(--surface-default)]',
  elevated: 'bg-[var(--surface-default)] shadow-[var(--shadow-card)]',
  dark: 'bg-[var(--surface-dark)] text-white',
  bordered: 'bg-transparent border border-[var(--border-subtle)]',
  glass: 'bg-[var(--surface-glass)] backdrop-blur-xl',
}

const PADDING_MAP = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-8',
}

const ROUNDED_MAP = {
  none: '',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
}

export function Surface({ variant = 'default', as: Component = 'div', padding = 'md', rounded = 'lg', className, children, ...props }: SurfaceProps) {
  return (
    <Component
      className={cn(
        VARIANT_MAP[variant],
        PADDING_MAP[padding],
        ROUNDED_MAP[rounded],
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}
