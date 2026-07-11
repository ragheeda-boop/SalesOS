import { cn } from "@salesos/ui"

type CardVariant = 'default' | 'dark' | 'bordered'
type CardPadding = 'sm' | 'md' | 'lg'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant
  padding?: CardPadding
  accent?: 'orange' | 'amber' | 'blue' | 'green' | 'purple' | 'red'
}

const VARIANT_CLASSES = {
  default: 'bg-white border border-[var(--border-default)] shadow-muhide-1',
  dark: 'bg-[var(--muhide-ink)] text-white',
  bordered: 'bg-white border border-[var(--border-default)]',
}

const PADDING_CLASSES = { sm: 'p-3', md: 'p-4', lg: 'p-5' }

const ACCENT_CLASSES = {
  orange: 'border-l-[3px] border-l-[var(--muhide-orange)]',
  amber: 'border-l-[3px] border-l-warning-600',
  blue: 'border-l-[3px] border-l-info-500',
  green: 'border-l-[3px] border-l-success-500',
  purple: 'border-l-[3px] border-l-purple-500',
  red: 'border-l-[3px] border-l-danger-500',
}

export function Card({ variant = 'default', padding = 'md', accent, className, children, ...props }: CardProps) {
  return (
      <div
        className={cn(
          'rounded-lg',
          VARIANT_CLASSES[variant],
          PADDING_CLASSES[padding],
          accent && ACCENT_CLASSES[accent],
          className
        )}
        {...props}
      >
        {children}
      </div>
  )
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-3', className)} {...props}>{children}</div>
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn(className)} {...props}>{children}</div>
}

export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mt-3 pt-3 border-t border-[var(--border-default)]', className)} {...props}>{children}</div>
}
