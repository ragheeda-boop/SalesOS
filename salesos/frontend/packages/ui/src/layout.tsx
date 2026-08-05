import { forwardRef, type ReactNode, type HTMLAttributes } from 'react'
import { cn } from './utils'

interface LayoutProps {
  children: ReactNode
  className?: string
}

export function Layout({ children, className }: LayoutProps) {
  return <div className={cn('flex h-screen', className)}>{children}</div>
}

export const LayoutHeader = forwardRef<HTMLElement, HTMLAttributes<HTMLElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <header
        ref={ref}
        className={cn(
          'sticky top-0 z-sticky flex h-14 items-center gap-4 border-b border-[var(--border-default)] bg-[var(--bg-primary)] px-4',
          className
        )}
        {...props}
      >
        {children}
      </header>
    )
  }
)
LayoutHeader.displayName = 'LayoutHeader'

export const LayoutSidebar = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('border-r border-[var(--border-default)] bg-[var(--bg-primary)]', className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)
LayoutSidebar.displayName = 'LayoutSidebar'

export const LayoutContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <main
        ref={ref}
        id="main-content"
        tabIndex={-1}
        className={cn('flex-1 overflow-auto p-6', className)}
        {...props}
      >
        {children}
      </main>
    )
  }
)
LayoutContent.displayName = 'LayoutContent'
