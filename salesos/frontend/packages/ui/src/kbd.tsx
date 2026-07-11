import { cn } from './utils'

interface KbdProps extends React.HTMLAttributes<HTMLElement> {
  children: string
}

export function Kbd({ className, children, ...props }: KbdProps) {
  return (
    <kbd
      className={cn(
        'inline-flex h-5 min-w-[20px] items-center justify-center rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-1.5 text-[11px] font-medium text-[var(--text-secondary)] shadow-muhide-1',
        className
      )}
      {...props}
    >
      {children}
    </kbd>
  )
}
