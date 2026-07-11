import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useCompany, useCompanySearch } from '../companyQueries'

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

describe('useCompany', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches a company', async () => {
    const company = { id: 'c-1', name_ar: 'شركة', cr_number: '123456', status: 'active', city: null, region: null, phone: null, email: null, confidence_score: 0.9, created_at: '2026-01-01', updated_at: '2026-07-10', branches: [], licenses: [], contacts: [] }
    mockedApi.getCompany.mockResolvedValue(company)
    const { result } = renderHook(() => useCompany('c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(company)
    expect(mockedApi.getCompany).toHaveBeenCalledWith('c-1', 'tenant-1')
  })

  it('does not fetch when id is empty', () => {
    const { result } = renderHook(() => useCompany(''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useCompanySearch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('searches companies', async () => {
    const response = { total: 1, page: 1, page_size: 10, items: [{ id: 'c-1', name_ar: 'شركة', cr_number: '123456', status: 'active', city: null, region: null, phone: null, email: null, confidence_score: null, created_at: '2026-01-01', updated_at: '2026-07-10' }] }
    mockedApi.searchCompanies.mockResolvedValue(response)
    const { result } = renderHook(() => useCompanySearch({ q: 'شركة' }), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.searchCompanies).toHaveBeenCalledWith({ q: 'شركة' }, 'tenant-1')
  })
})
