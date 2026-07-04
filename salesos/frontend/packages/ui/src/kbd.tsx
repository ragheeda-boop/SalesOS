import { cn } from './utils'

interface KbdProps extends React.HTMLAttributes<HTMLElement> {
  children: string
}

export function Kbd({ className, children, ...props }: KbdProps) {
  return (
    <kbd
      className={cn(
        'inline-flex h-5 min-w-[20px] items-center justify-center rounded border border-gray-300 bg-gray-50 px-1.5 text-[11px] font-medium text-gray-600 shadow-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300',
        className
      )}
      {...props}
    >
      {children}
    </kbd>
  )
}
