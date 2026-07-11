'use client'

import { cn } from '@salesos/ui'
import { X } from 'lucide-react'

interface SearchPillProps {
  label: string
  onRemove?: () => void
  className?: string
}

export function SearchPill({ label, onRemove, className }: SearchPillProps) {
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full bg-primary-50 px-2.5 py-1 text-[11px] font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300', className)}>
      {label}
      {onRemove && (
        <button onClick={onRemove} aria-label={`إزالة ${label}`} className="rounded-full p-0.5 hover:bg-primary-100 dark:hover:bg-primary-800/50">
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  )
}
