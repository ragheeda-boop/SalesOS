'use client'

import { useQuery } from '@tanstack/react-query'
import { searchKeys } from './search.keys'
import { searchApi } from './search.api'
import type { SearchQuery, SearchResponse } from '@salesos/search'

export function useSearch(query: SearchQuery) {
  return useQuery<SearchResponse>({
    queryKey: searchKeys.results(query),
    queryFn: () => searchApi(query),
    enabled: query.text.length >= 2,
    staleTime: 30_000,
  })
}

export function useAISearch(query: string, enabled = false) {
  return useQuery({
    queryKey: searchKeys.ai(query),
    queryFn: async () => {
      const res = await fetch('/api/v1/search/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query }),
      })
      if (!res.ok) throw new Error('AI search failed')
      return res.json()
    },
    enabled: enabled && query.length >= 2,
    staleTime: 60_000,
  })
}
