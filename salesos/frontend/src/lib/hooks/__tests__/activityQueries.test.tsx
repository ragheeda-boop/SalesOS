import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useEntityActivity } from '../activityQueries'

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

describe('useEntityActivity', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches entity activities', async () => {
    const activity = { entity_type: 'company', entity_id: 'c-1', items: [{ id: 'a-1', tenant_id: 't-1', actor: 'user', action: 'viewed', entity_type: 'company', entity_id: 'c-1', timestamp: '2026-07-10T10:00:00Z' }], total: 1 }
    mockedApi.getEntityActivities.mockResolvedValue(activity)
    const { result } = renderHook(() => useEntityActivity('company', 'c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(activity)
    expect(mockedApi.getEntityActivities).toHaveBeenCalledWith('company', 'c-1', 'tenant-1', 50)
  })

  it('does not fetch when entityType is empty', () => {
    const { result } = renderHook(() => useEntityActivity('', 'c-1'), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('does not fetch when entityId is empty', () => {
    const { result } = renderHook(() => useEntityActivity('company', ''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})
