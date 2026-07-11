import { cn } from "@salesos/ui"

interface PageLayoutProps {
  header?: React.ReactNode
  sidebar?: React.ReactNode
  children: React.ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
}

const MAX_WIDTH_MAP = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  full: 'max-w-full',
}

export function PageLayout({ header, sidebar, children, maxWidth = 'xl', className }: PageLayoutProps) {
  if (sidebar) {
    return (
      <div className="flex flex-1 h-full overflow-hidden">
        {sidebar}
        <div className="flex flex-col flex-1 min-w-0">
          {header}
          <main className={cn(
            'flex-1 overflow-y-auto',
            className
          )}>
            <div className={cn(
              'mx-auto px-6 py-6',
              MAX_WIDTH_MAP[maxWidth]
            )}>
              {children}
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
      {header}
      <main className={cn('flex-1 overflow-y-auto', className)}>
        <div className={cn(
          'mx-auto px-6 py-6',
          MAX_WIDTH_MAP[maxWidth]
        )}>
          {children}
        </div>
      </main>
    </div>
  )
}
