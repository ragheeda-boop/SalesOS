import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/hooks/useTenant')

import { getTenantId } from '@/lib/hooks/useTenant'
import { useOpportunities, useTasks, usePipeline, useCreateOpportunity, useCreateTask, useCompleteTask } from '../hooks'

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

describe('useOpportunities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches opportunities', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([{ id: 'o-1' }]) })

    const { result } = renderHook(() => useOpportunities(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([{ id: 'o-1' }])
  })

  it('filters by stage', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })

    renderHook(() => useOpportunities('won'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/opportunities?stage=won',
        expect.objectContaining({ headers: { 'X-Tenant-Id': 'tenant-1' } }),
      )
    })
  })
})

describe('useTasks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches tasks', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([{ id: 't-1' }]) })

    const { result } = renderHook(() => useTasks(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([{ id: 't-1' }])
  })
})

describe('usePipeline', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches pipeline', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ stages: [] }) })

    const { result } = renderHook(() => usePipeline(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({ stages: [] })
  })
})

describe('useCreateOpportunity', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('creates opportunity via mutation', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 'o-2' }) })

    const { result } = renderHook(() => useCreateOpportunity(), { wrapper: createWrapper() })

    result.current.mutate({ companyId: 'c-1', name: 'Deal' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})

describe('useCreateTask', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('creates task via mutation', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 't-2' }) })

    const { result } = renderHook(() => useCreateTask(), { wrapper: createWrapper() })

    result.current.mutate({ title: 'New Task' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})

describe('useCompleteTask', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('completes task via mutation', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 't-1', completed: true }) })

    const { result } = renderHook(() => useCompleteTask(), { wrapper: createWrapper() })

    result.current.mutate('t-1')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/tasks/t-1/complete',
      expect.objectContaining({ method: 'PUT' }),
    )
  })
})
