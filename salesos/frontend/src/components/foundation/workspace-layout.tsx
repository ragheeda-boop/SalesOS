import { cn } from "@salesos/ui"

interface WorkspaceLayoutProps {
  sidebar: React.ReactNode
  header: React.ReactNode
  tabs: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function WorkspaceLayout({ sidebar, header, tabs, children, className }: WorkspaceLayoutProps) {
  return (
    <div className="flex flex-1 h-full overflow-hidden">
      {sidebar}

      <div className="flex flex-col flex-1 min-w-0">
        {header}

        {tabs && (
          <div className="flex-shrink-0 border-b border-[var(--border-default)] bg-[var(--bg-primary)] px-4" role="tablist">
            {tabs}
          </div>
        )}

        <main className={cn(
          'flex-1 overflow-y-auto',
          className
        )} aria-label="Main content">
          {children}
        </main>
      </div>
    </div>
  )
}
