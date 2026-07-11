import { screen, fireEvent } from '@testing-library/react'
import { render, type RenderResult } from '@testing-library/react'
import { SearchProvider, useSearchContext } from '../search-provider'
import type { SearchResponse, SearchQuery } from '../types'
import { mockSearchResponse } from './mockSearchResults'
import type { ReactNode } from 'react'

export function createMockSearchEngine() {
  const mockResponse = mockSearchResponse()
  return {
    search: jest.fn().mockResolvedValue(mockResponse),
    suggest: jest.fn().mockResolvedValue([]),
    response: mockResponse,
  }
}

export function renderSearch(
  ui: ReactNode,
  options?: {
    onSearch?: (query: SearchQuery) => Promise<SearchResponse>
  },
): RenderResult {
  const engine = createMockSearchEngine()
  return render(
    <SearchProvider onSearch={options?.onSearch ?? engine.search}>
      {ui}
    </SearchProvider>,
  )
}

export { mockSearchResponse, mockSearchResult, mockSearchResults, mockSearchSuggestion } from './mockSearchResults'
