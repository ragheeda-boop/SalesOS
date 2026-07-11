'use client'

import { cn } from '@salesos/ui'
import { ArrowUpDown } from 'lucide-react'
import type { SortOption } from '@salesos/search'

interface SearchHeaderProps {
  total: number
  query: string
  sort?: SortOption
  onSortChange?: (sort: SortOption) => void
  className?: string
}

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'relevance', label: 'الأكثر صلة' },
  { value: 'recency', label: 'الأحدث' },
  { value: 'name', label: 'الاسم' },
]

export function SearchHeader({ total, query, sort = 'relevance', onSortChange, className }: SearchHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between px-4 py-3', className)}>
      <div>
        <h1 className="text-lg font-semibold text-[var(--text-primary)]">البحث</h1>
        <p className="text-xs text-[var(--text-muted)]">
          {total} نتيجة لـ "{query}"
        </p>
      </div>
      {onSortChange && (
        <div className="flex items-center gap-1">
          <ArrowUpDown className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onSortChange(opt.value)}
              className={cn(
                'rounded-lg px-2 py-1 text-xs transition',
                sort === opt.value
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                  : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]',
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
