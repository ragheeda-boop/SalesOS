import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useTasks, useCompleteTask } from '../taskQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

const sampleTasks = [
  { id: 't-1', title: 'Follow up', priority: 'high', source: 'nba', company_id: 'c-1', completed: false, created_at: '2026-07-10T10:00:00Z' },
  { id: 't-2', title: 'Send proposal', priority: 'medium', source: 'manual', completed: false, created_at: '2026-07-09T10:00:00Z' },
]

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useTasks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches tasks', async () => {
    mockedApi.listTasks.mockResolvedValue(sampleTasks)
    const { result } = renderHook(() => useTasks(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleTasks)
    expect(mockedApi.listTasks).toHaveBeenCalledWith('tenant-1', undefined)
  })

  it('fetches tasks with priority filter', async () => {
    mockedApi.listTasks.mockResolvedValue(sampleTasks)
    const { result } = renderHook(() => useTasks('high'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.listTasks).toHaveBeenCalledWith('tenant-1', 'high')
  })
})

describe('useCompleteTask', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('completes a task', async () => {
    mockedApi.completeTask.mockResolvedValue(sampleTasks[0])
    const { result } = renderHook(() => useCompleteTask(), { wrapper: createWrapper() })

    result.current.mutate({ taskId: 't-1' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.completeTask).toHaveBeenCalledWith('t-1')
  })
})
