'use client'

import { useState, useCallback, useEffect } from 'react'
import { cn } from '@salesos/ui'
import { SearchProvider, useSearchContext } from '@salesos/search'
import type { SearchResult, SearchQuery, SearchResponse, SortOption } from '@salesos/search'
import { SearchBar, SearchHeader, SearchResultCard, SearchSection, SearchLoading, SearchEmpty, SearchError, SearchPill, SearchFilters } from '../components'
import { searchApi } from '@/application/search/search.api'
import { AIAnswerCard } from '../ai-search/AIAnswer'

function SearchPageInner() {
  const { query, results, total, isLoading, isError, error, facets, aiAnswer, search, setQuery, refetch } = useSearchContext()
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sort, setSort] = useState<SortOption>('relevance')
  const [page, setPage] = useState(1)

  const handleSearch = useCallback((text: string) => {
    setQuery({ text, page: 1, sort })
    search(text)
  }, [setQuery, search, sort])

  const handleSortChange = useCallback((newSort: SortOption) => {
    setSort(newSort)
    setQuery({ sort: newSort })
  }, [setQuery])

  const handleFilterToggle = useCallback((field: string, value: string) => {
    setSelectedFilters((prev) => {
      const current = prev[field] ?? []
      const updated = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
      return { ...prev, [field]: updated }
    })
  }, [])

  const activePills = Object.entries(selectedFilters).flatMap(([field, values]) =>
    values.map((v) => ({ field, value: v }))
  )
  const hasQuery = query.text.trim().length >= 2

  return (
    <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6">
      {/* Filters sidebar */}
      {facets.length > 0 && (
        <aside className="hidden w-64 shrink-0 lg:block">
          <SearchFilters
            facets={facets}
            selectedFilters={selectedFilters}
            onToggle={handleFilterToggle}
          />
        </aside>
      )}

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="mb-6">
          <SearchBar onSearch={handleSearch} variant="hero" placeholder="ابحث في الشركات، الأشخاص، الإشارات…" />
        </div>

        {/* Active filters */}
        {activePills.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1.5 px-4">
            {activePills.map((pill) => (
              <SearchPill
                key={`${pill.field}-${pill.value}`}
                label={`${pill.field}: ${pill.value}`}
                onRemove={() => handleFilterToggle(pill.field, pill.value)}
              />
            ))}
          </div>
        )}

        {/* AI Answer */}
        {aiAnswer && hasQuery && (
          <div className="mb-4 px-4">
            <AIAnswerCard answer={aiAnswer} />
          </div>
        )}

        {/* Header */}
        {hasQuery && (
          <SearchHeader
            total={total}
            query={query.text}
            sort={sort}
            onSortChange={handleSortChange}
          />
        )}

        {/* Content */}
        {hasQuery && isLoading && <SearchLoading count={5} />}
        {hasQuery && isError && <SearchError message={error?.message} onRetry={refetch} />}
        {hasQuery && !isLoading && !isError && results.length === 0 && <SearchEmpty query={query.text} />}

        {hasQuery && results.length > 0 && (
          <>
            <div className="divide-y divide-[var(--border-color)]">
              {results.map((r, i) => (
                <SearchResultCard key={r.id} result={r} highlighted={false} />
              ))}
            </div>

            {/* Pagination */}
            {total > 10 && (
              <div className="flex items-center justify-center gap-2 py-6">
                {Array.from({ length: Math.min(5, Math.ceil(total / 10)) }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setPage(i + 1)}
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded-lg text-xs transition',
                      page === i + 1
                        ? 'bg-primary-500 text-white'
                        : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]',
                    )}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {/* Idle state */}
        {!hasQuery && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-lg font-medium text-[var(--text-muted)]">ابحث في المنصة</p>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              اكتب للبحث في الشركات، الأشخاص، الإشارات، والمزيد
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export function SearchPage() {
  return (
    <SearchProvider onSearch={(q) => searchApi(q)}>
      <SearchPageInner />
    </SearchProvider>
  )
}
