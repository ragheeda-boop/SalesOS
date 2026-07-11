import type { SearchResult, SearchSuggestion, SearchResponse, SearchFacet } from '../types'

const now = new Date().toISOString()

export function mockSearchResult(overrides?: Partial<SearchResult>): SearchResult {
  return {
    id: 'result_1',
    entityType: 'company',
    title: 'شركة أرامكو السعودية',
    subtitle: 'شركة نفط وغاز وطنية',
    description: 'أكبر شركة نفط في العالم من حيث الإنتاج…',
    score: 0.95,
    confidence: 0.92,
    highlights: [],
    badges: [{ label: 'نشط', variant: 'success' }],
    actions: [{ id: 'view', label: 'عرض', handler: 'navigate' }],
    source: 'postgresql',
    updatedAt: now,
    ...overrides,
  }
}

export function mockSearchResults(count = 5, overrides?: Partial<SearchResult>): SearchResult[] {
  return Array.from({ length: count }, (_, i) =>
    mockSearchResult({
      id: `result_${i + 1}`,
      title: i === 0 ? 'شركة أرامكو السعودية' : `شركة ${i + 1}`,
      score: Math.max(0, 0.95 - i * 0.1),
      ...overrides,
    }),
  )
}

export function mockSearchSuggestion(overrides?: Partial<SearchSuggestion>): SearchSuggestion {
  return {
    text: 'شركات في قطاع الطاقة',
    type: 'query',
    score: 0.9,
    ...overrides,
  }
}

export function mockSearchResponse(overrides?: Partial<SearchResponse>): SearchResponse {
  return {
    results: mockSearchResults(),
    total: 42,
    page: 1,
    pageSize: 10,
    facets: [
      { field: 'industry', label: 'القطاع', values: [{ value: 'energy', count: 15 }, { value: 'healthcare', count: 10 }] },
      { field: 'region', label: 'المنطقة', values: [{ value: 'riyadh', count: 20 }, { value: 'jeddah', count: 12 }] },
    ],
    queryInterpretation: {
      original: 'energy companies',
      interpreted: 'شركات في قطاع الطاقة',
      entities: [{ type: 'industry', value: 'energy' }],
      intent: 'search',
      confidence: 0.9,
    },
    timing: { total: 150, fullText: 50, semantic: 80, graph: 20, ai: 0, permissions: 0 },
    ...overrides,
  }
}
