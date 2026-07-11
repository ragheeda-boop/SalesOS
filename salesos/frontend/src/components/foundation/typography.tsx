import { cn } from "@salesos/ui"
import { TYPOGRAPHY, FONT_FAMILY } from "@salesos/design-language"

type TypographyVariant = keyof typeof TYPOGRAPHY

interface TypographyProps extends React.HTMLAttributes<HTMLElement> {
  variant?: TypographyVariant
  as?: React.ElementType
  weight?: 400 | 500 | 600 | 700
  color?: 'primary' | 'secondary' | 'muted' | 'disabled' | 'brand' | 'white'
  truncate?: boolean
  children: React.ReactNode
}

const TAG_MAP: Record<TypographyVariant, React.ElementType> = {
  h1: 'h1', h2: 'h2', h3: 'h3', h4: 'h4', h5: 'h5', h6: 'h6',
  body: 'p', 'body-sm': 'p', caption: 'span', label: 'label', code: 'code', kbd: 'kbd',
}

const COLOR_MAP = {
  primary: 'text-[var(--text-primary)]',
  secondary: 'text-[var(--text-secondary)]',
  muted: 'text-[var(--text-muted)]',
  disabled: 'text-[var(--text-disabled)]',
  brand: 'text-[var(--muhide-orange)]',
  white: 'text-white',
}

export function Typography({ variant = 'body', as, weight, color = 'primary', truncate, className, children, ...props }: TypographyProps) {
  const Component = as || TAG_MAP[variant]
  const token = TYPOGRAPHY[variant]
  const isDisplay = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(variant)

  return (
    <Component
      className={cn(
        isDisplay && 'font-display',
        !isDisplay && variant !== 'code' && variant !== 'kbd' && 'font-sans',
        variant === 'code' && 'font-mono',
        variant === 'kbd' && 'font-mono',
        COLOR_MAP[color],
        weight && `font-[${weight}]`,
        truncate && 'truncate',
        className
      )}
      style={{
        fontSize: `${token.size}px`,
        lineHeight: token.lineHeight,
        fontWeight: weight || token.weight,
        letterSpacing: token.letterSpacing,
      }}
      {...props}
    >
      {children}
    </Component>
  )
}
