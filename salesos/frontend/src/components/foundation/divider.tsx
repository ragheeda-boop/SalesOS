import { cn } from "@salesos/ui"

type DividerVariant = 'full' | 'light' | 'dark'

interface DividerProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: DividerVariant
  label?: string
}

const VARIANT_MAP: Record<DividerVariant, string> = {
  full: 'my-6 border-t border-[var(--border-subtle)]',
  light: 'my-3 border-t border-[var(--border-muted)]',
  dark: 'my-6 border-t-2 border-[var(--border-strong)]',
}

export function Divider({ variant = 'full', label, className, ...props }: DividerProps) {
  if (label) {
    return (
      <div className={cn('flex items-center gap-3 my-6', className)} role="separator" aria-orientation="horizontal" aria-label={label} {...props}>
        <span className={cn('flex-1 border-t', variant === 'dark' ? 'border-[var(--border-strong)]' : 'border-[var(--border-subtle)]')} aria-hidden="true" />
        <span className="text-sm text-[var(--text-muted)] whitespace-nowrap">{label}</span>
        <span className={cn('flex-1 border-t', variant === 'dark' ? 'border-[var(--border-strong)]' : 'border-[var(--border-subtle)]')} aria-hidden="true" />
      </div>
    )
  }

  return (
    <div
      className={cn(VARIANT_MAP[variant], className)}
      role="separator"
      aria-orientation="horizontal"
      {...props}
    />
  )
}
