import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('../search.api')

import { searchApi } from '../search.api'
import { useSearch, useAISearch } from '../search.hooks'

const mockedSearchApi = searchApi as jest.MockedFunction<typeof searchApi>

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useSearch', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('fetches search results', async () => {
    const response = { resultIds: [], results: [] as any[], total: 0, page: 1, pageSize: 10, facets: {} }
    mockedSearchApi.mockResolvedValue(response as any)

    const { result } = renderHook(() => useSearch({ text: 'test', filters: {}, page: 1, pageSize: 10 }), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
  })

  it('does not fetch when query text is too short', () => {
    const { result } = renderHook(() => useSearch({ text: 'a', filters: {}, page: 1, pageSize: 10 }), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useAISearch', () => {
  const mockFetch = jest.fn()
  beforeEach(() => {
    jest.clearAllMocks()
    global.fetch = mockFetch
  })

  it('fetches AI search when enabled', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ answer: 'AI answer' }) })

    const { result } = renderHook(() => useAISearch('what is sales?', true), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({ answer: 'AI answer' })
  })

  it('does not fetch when disabled', () => {
    const { result } = renderHook(() => useAISearch('test', false), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('throws on error response', async () => {
    mockFetch.mockResolvedValue({ ok: false })

    const { result } = renderHook(() => useAISearch('test', true), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
