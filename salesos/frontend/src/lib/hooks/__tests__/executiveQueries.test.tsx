import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useExecutiveDashboard } from '../executiveQueries'

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

describe('useExecutiveDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches executive dashboard data', async () => {
    const response = {
      revenue: { total_booked: 1000000, total_pipeline: 2000000, weighted_pipeline: 1500000, forecast: 1200000, growth_percent: 15 },
      team: { total_employees: 50, active_employees: 45, top_performers: [], avg_win_rate: 0.4 },
      risk: { expiring_contracts: 3, stalled_deals: 5, inactive_companies: 10, low_pipeline_employees: 2 },
      health: { overall_health: 'good', data_completeness: 85, sync_status: 'synced', last_activity: '2026-07-10' },
      pipeline: { total_deals: 20, total_value: 2000000, won_deals: 8, lost_deals: 3, win_rate: 0.4, avg_deal_size: 100000, by_stage: [] },
      renewals: { due_next_30_days: 2, due_next_90_days: 5, total_renewal_value: 500000, at_risk: [] },
      growth: { new_companies_30d: 10, new_contacts_30d: 25, new_opportunities_30d: 5, new_contracts_30d: 3 },
    }
    mockedApi.getExecutiveDashboard.mockResolvedValue(response)
    const { result } = renderHook(() => useExecutiveDashboard(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.getExecutiveDashboard).toHaveBeenCalledWith('tenant-1')
  })
})
