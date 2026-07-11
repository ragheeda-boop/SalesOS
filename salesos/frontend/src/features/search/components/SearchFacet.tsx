'use client'

import { cn } from '@salesos/ui'
import { useState, useCallback } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { SearchFacet } from '@salesos/search'

interface SearchFacetProps {
  facet: SearchFacet
  selectedValues?: string[]
  onToggle: (value: string) => void
  className?: string
}

export function SearchFacetGroup({ facet, selectedValues = [], onToggle, className }: SearchFacetProps) {
  const [open, setOpen] = useState(true)

  return (
    <div className={cn('space-y-1', className)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2 text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)]"
      >
        {facet.label}
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>
      {open && (
        <div className="space-y-0.5 px-3">
          {facet.values.map((v) => {
            const selected = selectedValues.includes(v.value)
            return (
              <button
                key={v.value}
                onClick={() => onToggle(v.value)}
                className={cn(
                  'flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-xs transition',
                  selected
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]',
                )}
              >
                <span>{v.value}</span>
                <span className="rounded bg-[var(--bg-tertiary)] px-1 py-0.5 text-[10px]">{v.count}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
