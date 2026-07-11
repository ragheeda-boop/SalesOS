'use client'

import { cn } from '@salesos/ui'
import type { ReactNode } from 'react'

interface SearchSectionProps {
  title: string
  count?: number
  icon?: ReactNode
  children: ReactNode
  collapsible?: boolean
  defaultOpen?: boolean
  className?: string
}

export function SearchSection({ title, count, icon, children, collapsible, defaultOpen = true, className }: SearchSectionProps) {
  return (
    <section className={cn('space-y-1', className)}>
      <div className={cn('flex items-center gap-2 px-4 py-2', collapsible && 'cursor-pointer hover:bg-[var(--bg-tertiary)]')}>
        {icon && <span className="text-[var(--text-muted)]">{icon}</span>}
        <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">{title}</h3>
        {count !== undefined && (
          <span className="rounded-full bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
            {count}
          </span>
        )}
      </div>
      <div className={cn(!defaultOpen && 'hidden')}>
        {children}
      </div>
    </section>
  )
}
