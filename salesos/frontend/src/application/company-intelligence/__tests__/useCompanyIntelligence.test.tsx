import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/hooks/useTenant')

import { getTenantId } from '@/lib/hooks/useTenant'
import { useCompanyIntelligence } from '../useCompanyIntelligence'

const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>
const mockFetch = jest.fn()
global.fetch = mockFetch

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useCompanyIntelligence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches company intelligence', async () => {
    const data = { companyId: 'c-1', generatedAt: '2026-07-11T12:00:00Z', dna: null, aiRecommendation: null, decisionMakers: [], relationships: { nodes: [], edges: [] }, timeline: [], signals: [], government: [], documents: [], buyingJourney: null, goldenRecord: [], firmographic: null }
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(data) })

    const { result } = renderHook(() => useCompanyIntelligence('c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(data)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/companies/c-1/intelligence', {
      headers: { 'X-Tenant-Id': 'tenant-1' },
    })
  })

  it('does not fetch when companyId is empty', () => {
    const { result } = renderHook(() => useCompanyIntelligence(''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('throws on error response', async () => {
    mockFetch.mockResolvedValue({ ok: false })

    const { result } = renderHook(() => useCompanyIntelligence('c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
