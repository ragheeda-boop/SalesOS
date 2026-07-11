'use client'

import { cn } from '@salesos/ui'
import { Search, Clock, TrendingUp } from 'lucide-react'
import type { SearchSuggestion as SearchSuggestionType } from '@salesos/search'

interface SearchSuggestionProps {
  suggestion: SearchSuggestionType
  onClick: (suggestion: SearchSuggestionType) => void
  highlighted?: boolean
}

export function SearchSuggestion({ suggestion, onClick, highlighted }: SearchSuggestionProps) {
  const icon = suggestion.type === 'recent' ? <Clock className="h-3.5 w-3.5" /> : suggestion.type === 'query' ? <Search className="h-3.5 w-3.5" /> : <TrendingUp className="h-3.5 w-3.5" />

  return (
    <button
      role="option"
      aria-selected={highlighted}
      className={cn(
        'flex w-full items-center gap-3 px-4 py-2 text-sm transition',
        highlighted
          ? 'bg-primary-50 dark:bg-primary-900/20'
          : 'hover:bg-[var(--bg-tertiary)]',
      )}
      onClick={() => onClick(suggestion)}
    >
      <span className="text-[var(--text-muted)]">{icon}</span>
      <span className="text-[var(--text-primary)]">{suggestion.text}</span>
    </button>
  )
}
