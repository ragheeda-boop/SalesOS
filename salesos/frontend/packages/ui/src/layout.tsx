import { forwardRef, type ReactNode, type HTMLAttributes } from 'react'
import { cn } from './utils'

interface LayoutProps {
  children: ReactNode
  className?: string
}

export function Layout({ children, className }: LayoutProps) {
  return <div className={cn('flex h-screen', className)}>{children}</div>
}

interface LayoutHeaderProps extends HTMLAttributes<HTMLElement> {}

export const LayoutHeader = forwardRef<HTMLElement, LayoutHeaderProps>(
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

interface LayoutSidebarProps extends HTMLAttributes<HTMLDivElement> {}

export const LayoutSidebar = forwardRef<HTMLDivElement, LayoutSidebarProps>(
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

interface LayoutContentProps extends HTMLAttributes<HTMLDivElement> {}

export const LayoutContent = forwardRef<HTMLDivElement, LayoutContentProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <main
        ref={ref}
        className={cn('flex-1 overflow-auto p-6', className)}
        {...props}
      >
        {children}
      </main>
    )
  }
)
LayoutContent.displayName = 'LayoutContent'
