'use client'

import { cn } from '@salesos/ui'
import { ListFilter } from 'lucide-react'
import type { SearchFacet } from '@salesos/search'
import { SearchFacetGroup } from './SearchFacet'

interface SearchFiltersProps {
  facets: SearchFacet[]
  selectedFilters: Record<string, string[]>
  onToggle: (field: string, value: string) => void
  className?: string
}

export function SearchFilters({ facets, selectedFilters, onToggle, className }: SearchFiltersProps) {
  return (
    <aside className={cn('space-y-2', className)}>
      <div className="flex items-center gap-2 px-3 py-2">
        <ListFilter className="h-4 w-4 text-[var(--text-muted)]" />
        <span className="text-xs font-semibold text-[var(--text-muted)] uppercase">تصفية</span>
      </div>
      {facets.map((facet) => (
        <SearchFacetGroup
          key={facet.field}
          facet={facet}
          selectedValues={selectedFilters[facet.field] ?? []}
          onToggle={(value) => onToggle(facet.field, value)}
        />
      ))}
    </aside>
  )
}
