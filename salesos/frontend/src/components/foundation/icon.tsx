import { cn } from "@salesos/ui"

interface IconProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'muted' | 'brand' | 'white' | 'current'
  className?: string
  children: React.ReactNode
  label?: string
}

const SIZE_MAP = { sm: 14, md: 16, lg: 20, xl: 24 }
const COLOR_MAP = {
  primary: 'text-[var(--text-primary)]',
  secondary: 'text-[var(--text-secondary)]',
  muted: 'text-[var(--text-muted)]',
  brand: 'text-[var(--muhide-orange)]',
  white: 'text-white',
  current: 'text-current',
}

export function Icon({ size = 'md', color = 'current', className, children, label }: IconProps) {
  return (
    <span
      className={cn('inline-flex items-center justify-center', COLOR_MAP[color], className)}
      style={{ width: SIZE_MAP[size], height: SIZE_MAP[size] }}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? 'img' : undefined}
    >
      {children}
    </span>
  )
}
