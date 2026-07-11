import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId, useTenant } from '../useTenant'
import { useAdminHealth, useAdminMetrics, useDlq, useRetryDlq } from '../adminQueries'

(useTenant as jest.Mock).mockReturnValue({ tenantId: 'tenant-1' })

const mockedApi = api as jest.Mocked<typeof api>

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useAdminHealth', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('fetches admin health', async () => {
    const health = { status: 'healthy', checks: { database: 'ok', redis: 'ok' }, pipeline: { status: 'running' } }
    mockedApi.getAdminHealth.mockResolvedValue(health)
    const { result } = renderHook(() => useAdminHealth(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(health)
  })
})

describe('useAdminMetrics', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('fetches admin metrics', async () => {
    mockedApi.getAdminMetrics.mockResolvedValue('{"data":"ok"}')
    const { result } = renderHook(() => useAdminMetrics(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBe('{"data":"ok"}')
  })
})

describe('useDlq', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('fetches DLQ entries', async () => {
    const dlqResponse = { total: 1, page: 1, page_size: 10, items: [{ id: 1, source_slug: 'cr', cr_number: null, stage: 'enrich', error_message: 'Failed', error_type: null, retry_count: 0, max_retries: 3, status: 'failed', created_at: '2026-07-10T10:00:00Z', last_retry_at: null }] }
    mockedApi.listDlq.mockResolvedValue(dlqResponse)
    const { result } = renderHook(() => useDlq({ status: 'failed' }), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(dlqResponse)
  })
})

describe('useRetryDlq', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('retries DLQ entries', async () => {
    mockedApi.retryDlq.mockResolvedValue({ processed: 5, retried: 5, resolved: 3, still_failed: 2 })
    const { result } = renderHook(() => useRetryDlq(), { wrapper: createWrapper() })

    result.current.mutate(10)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.retryDlq).toHaveBeenCalledWith('tenant-1', 10)
  })
})
