'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
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
      const res = await api.post('/api/v1/search/ai', { text: query })
      return res.data
    },
    enabled: enabled && query.length >= 2,
    staleTime: 60_000,
  })
}
