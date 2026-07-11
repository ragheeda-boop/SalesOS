'use client'

import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from 'react'
import type { SearchQuery, SearchResult, SearchResponse, SearchFacet, AIAnswer, SearchSuggestion, SearchHistoryEntry, SearchContextValue } from './types'
import { searchTelemetry, createTelemetryTimer } from './search-telemetry'
import { queryToKey, isQueryEmpty } from './query-builder'

interface SearchProviderProps {
  children: ReactNode
  initialQuery?: Partial<SearchQuery>
  onSearch?: (query: SearchQuery) => Promise<SearchResponse>
  onSuggest?: (prefix: string) => Promise<SearchSuggestion[]>
}

const SearchContext = createContext<SearchContextValue | null>(null)

export function SearchProvider({ children, initialQuery, onSearch, onSuggest }: SearchProviderProps) {
  const [query, setQueryState] = useState<SearchQuery>({ text: '', ...initialQuery })
  const [results, setResults] = useState<SearchResult[]>([])
  const [total, setTotal] = useState(0)
  const [facets, setFacets] = useState<SearchFacet[]>([])
  const [aiAnswer, setAiAnswer] = useState<AIAnswer | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [history, setHistory] = useState<SearchHistoryEntry[]>([])

  const setQuery = useCallback((partial: Partial<SearchQuery>) => {
    setQueryState((prev) => ({ ...prev, ...partial }))
  }, [])

  const search = useCallback(async (text: string) => {
    if (!text || text.trim().length < 2) return
    const timer = createTelemetryTimer()
    setIsLoading(true)
    setIsError(false)
    setError(null)
    setAiAnswer(null)

    const newQuery = { ...query, text, page: 1 }

    try {
      if (onSearch) {
        const response = await onSearch(newQuery)
        setResults(response.results)
        setTotal(response.total)
        setFacets(response.facets ?? [])
        if (response.aiAnswer) setAiAnswer(response.aiAnswer)
      }
      timer.stop('search.query', { query: text, resultCount: results.length })

      setHistory((prev) => {
        const entry: SearchHistoryEntry = { id: Date.now().toString(), text, timestamp: Date.now(), resultCount: total }
        return [entry, ...prev.filter((h) => h.text !== text)].slice(0, 50)
      })
    } catch (err) {
      setIsError(true)
      setError(err instanceof Error ? err : new Error('Search failed'))
      searchTelemetry.error('Search failed', text)
    } finally {
      setIsLoading(false)
    }
  }, [query, onSearch, results.length, total])

  const clearSearch = useCallback(() => {
    setQueryState({ text: '' })
    setResults([])
    setTotal(0)
    setFacets([])
    setAiAnswer(null)
    setIsLoading(false)
    setIsError(false)
    setError(null)
  }, [])

  const value = useMemo<SearchContextValue>(
    () => ({
      query, results, total, facets, aiAnswer, isLoading, isError, error,
      suggestions, history,
      setQuery, search, clearSearch,
      refetch: () => search(query.text),
    }),
    [query, results, total, facets, aiAnswer, isLoading, isError, error, suggestions, history, setQuery, search, clearSearch],
  )

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>
}

export function useSearchContext(): SearchContextValue {
  const ctx = useContext(SearchContext)
  if (!ctx) throw new Error('useSearchContext must be used within <SearchProvider>')
  return ctx
}
