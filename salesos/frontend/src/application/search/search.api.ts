import type { SearchQuery, SearchResponse } from '@salesos/search'

export async function searchApi(query: SearchQuery): Promise<SearchResponse> {
  const res = await fetch('/api/v1/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(query),
  })
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}

export async function suggestApi(prefix: string): Promise<SearchResponse['results']> {
  const res = await fetch('/api/v1/search/suggest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prefix, limit: 5 }),
  })
  if (!res.ok) return []
  return res.json()
}
