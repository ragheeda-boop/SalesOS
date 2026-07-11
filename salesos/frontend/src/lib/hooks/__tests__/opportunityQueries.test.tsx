import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useOpportunities, useCreateOpportunity, useAdvanceOpportunity, useCloseWon, useCloseLost } from '../opportunityQueries'

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

describe('useOpportunities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches opportunities', async () => {
    const response = { items: [{ id: 'o-1', name: 'Deal', stage: 'qualifying', value: 50000, company_id: 'c-1' }], total: 1 }
    mockedApi.listOpportunities.mockResolvedValue(response)
    const { result } = renderHook(() => useOpportunities(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
  })
})

describe('useCreateOpportunity', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('creates an opportunity', async () => {
    const created = { id: 'o-2', name: 'New Deal', stage: 'identified', value: 100000, company_id: 'c-1' }
    mockedApi.createOpportunity.mockResolvedValue(created)
    const { result } = renderHook(() => useCreateOpportunity(), { wrapper: createWrapper() })

    result.current.mutate({ companyId: 'c-1', name: 'New Deal', value: 100000 })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.createOpportunity).toHaveBeenCalledWith('tenant-1', 'c-1', 'New Deal', 100000)
  })
})

describe('useAdvanceOpportunity', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('advances opportunity stage', async () => {
    mockedApi.advanceOpportunity.mockResolvedValue({ id: 'o-1', stage: 'developing' })
    const { result } = renderHook(() => useAdvanceOpportunity(), { wrapper: createWrapper() })

    result.current.mutate({ opportunityId: 'o-1', toStage: 'developing' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.advanceOpportunity).toHaveBeenCalledWith('o-1', 'developing')
  })
})

describe('useCloseWon', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('closes won with amount', async () => {
    mockedApi.closeWon.mockResolvedValue({ id: 'o-1', stage: 'won' })
    const { result } = renderHook(() => useCloseWon(), { wrapper: createWrapper() })

    result.current.mutate({ opportunityId: 'o-1', amount: 100000 })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.closeWon).toHaveBeenCalledWith('o-1', 100000)
  })
})

describe('useCloseLost', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('closes lost with reason', async () => {
    mockedApi.closeLost.mockResolvedValue({ id: 'o-1', stage: 'lost' })
    const { result } = renderHook(() => useCloseLost(), { wrapper: createWrapper() })

    result.current.mutate({ opportunityId: 'o-1', reason: 'Budget' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.closeLost).toHaveBeenCalledWith('o-1', 'Budget')
  })
})
