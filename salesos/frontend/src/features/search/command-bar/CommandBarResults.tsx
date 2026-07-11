'use client'


import { useSearchContext, SearchHighlight } from '@salesos/search'
import type { SearchResult } from '@salesos/search'
import { SearchSection, SearchResultCard, SearchLoading, SearchEmpty } from '../components'
import { Building2, User, FileText, Sparkles, Activity, Clock } from 'lucide-react'

interface CommandBarResultsProps {
  highlightedIndex: number
  onResultClick: (result: SearchResult) => void
  onSuggestionClick: (text: string) => void
  onHistoryClick: (text: string) => void
}

export function CommandBarResults({ highlightedIndex, onResultClick, onSuggestionClick, onHistoryClick }: CommandBarResultsProps) {
  const { results, total, isLoading, query, suggestions, history } = useSearchContext()
  const hasInput = query.text.trim().length >= 2

  if (isLoading) return <SearchLoading count={3} />

  if (hasInput && results.length === 0 && !isLoading) {
    return <SearchEmpty query={query.text} />
  }

  let idx = 0

  return (
    <div className="max-h-96 overflow-y-auto">
      {/* Suggestions */}
      {!hasInput && suggestions.length > 0 && (
        <SearchSection title="اقتراحات" icon={<Sparkles className="h-3.5 w-3.5" />}>
          {suggestions.map((s, i) => {
            const currentIdx = idx++
            return (
              <button
                key={`sug-${i}`}
                role="option"
                aria-selected={highlightedIndex === currentIdx}
                className={cn(
                  'flex w-full items-center gap-3 px-4 py-2 text-sm transition',
                  highlightedIndex === currentIdx ? 'bg-primary-50 dark:bg-primary-900/20' : 'hover:bg-[var(--bg-tertiary)]',
                )}
                onClick={() => onSuggestionClick(s.text)}
              >
                <Sparkles className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                <span className="text-[var(--text-primary)]">{s.text}</span>
              </button>
            )
          })}
        </SearchSection>
      )}

      {/* History */}
      {!hasInput && history.length > 0 && (
        <SearchSection title="آخر البحوث" icon={<Clock className="h-3.5 w-3.5" />}>
          {history.slice(0, 5).map((h) => {
            const currentIdx = idx++
            return (
              <button
                key={h.id}
                role="option"
                aria-selected={highlightedIndex === currentIdx}
                className={cn(
                  'flex w-full items-center gap-3 px-4 py-2 text-sm transition',
                  highlightedIndex === currentIdx ? 'bg-primary-50 dark:bg-primary-900/20' : 'hover:bg-[var(--bg-tertiary)]',
                )}
                onClick={() => onHistoryClick(h.text)}
              >
                <Clock className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                <span className="text-[var(--text-primary)]">{h.text}</span>
              </button>
            )
          })}
        </SearchSection>
      )}

      {/* Results */}
      {hasInput && results.length > 0 && (
        <SearchSection title="النتائج" count={total}>
          {results.slice(0, 10).map((r) => {
            const currentIdx = idx++
            return (
              <SearchResultCard
                key={r.id}
                result={r}
                highlighted={highlightedIndex === currentIdx}
                onClick={onResultClick}
              />
            )
          })}
        </SearchSection>
      )}
    </div>
  )
}

import { cn } from '@salesos/ui'
