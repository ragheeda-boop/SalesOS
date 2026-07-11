import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useSearch } from '../searchQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches search results', async () => {
    const response = { query: 'test', strategy: 'hybrid', total: 1, took_ms: 100, items: [{ id: '1', type: 'company', score: 0.9, data: {} }] }
    mockedApi.unifiedSearch.mockResolvedValue(response)
    const { result } = renderHook(() => useSearch({ q: 'test', strategy: 'hybrid' }), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.unifiedSearch).toHaveBeenCalledWith({ q: 'test', strategy: 'hybrid' }, 'tenant-1')
  })

  it('does not fetch when query is too short', () => {
    const { result } = renderHook(() => useSearch({ q: 'a' }), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})
