'use client'

import { cn } from '@salesos/ui'
import type { ReactNode } from 'react'

interface SearchGroupProps {
  label: string
  count?: number
  children: ReactNode
  className?: string
}

export function SearchGroup({ label, count, children, className }: SearchGroupProps) {
  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center gap-2 px-4 py-1">
        <span className="text-[10px] font-medium text-[var(--text-muted)]">{label}</span>
        {count !== undefined && (
          <span className="text-[10px] text-[var(--text-muted)]">({count})</span>
        )}
      </div>
      <div className="space-y-0.5">{children}</div>
    </div>
  )
}
