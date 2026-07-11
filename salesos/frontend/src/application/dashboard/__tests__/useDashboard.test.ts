import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('../api')
jest.mock('@/lib/hooks/useTenant')
jest.mock('../dashboard.mapper')

import { getDashboard } from '../api'
import { getTenantId } from '@/lib/hooks/useTenant'
import { mapDashboard } from '../dashboard.mapper'
import { useDashboard } from '../useDashboard'

const mockedGetDashboard = getDashboard as jest.MockedFunction<typeof getDashboard>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>
const mockedMapDashboard = mapDashboard as jest.MockedFunction<typeof mapDashboard>

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
    mockedGetDashboard.mockResolvedValue({ totalTracked: 42 })
    mockedMapDashboard.mockReturnValue({ generatedAt: null, period: 'today', totalTracked: 42, missionCenter: null, decisionQueue: null, intelligenceFeed: null, aiBrief: null, marketPulse: null, recentActivity: null })
  })

  it('fetches and maps dashboard data', async () => {
    const { result } = renderHook(() => useDashboard(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedGetDashboard).toHaveBeenCalledWith('tenant-1')
    expect(mockedMapDashboard).toHaveBeenCalledWith({ totalTracked: 42 })
    expect(result.current.data?.totalTracked).toBe(42)
  })
})
