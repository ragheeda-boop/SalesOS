import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useEmployee360, useMy360 } from '../employeeQueries'

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

describe('useEmployee360', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches employee 360 data', async () => {
    const response = {
      profile: { id: 'e-1', full_name: 'Ahmed', full_name_ar: 'أحمد', email: 'a@b.com', role: 'manager', phone: null, avatar_url: null, is_active: true, tenant_id: 't-1', created_at: '2026-01-01', team: [], manager: null },
      portfolio: { companies: [], contacts: [], pipeline: [], revenue: 0, contracts: [], projects: [] },
      calendar_intelligence: { today_count: 0, week_count: 0, month_count: 0, total_hours: 0, avg_duration_minutes: 0, unique_companies_met: 0, upcoming: [] },
      email_intelligence: { sent: 0, received: 0, replies: 0, avg_response_hours: 0, top_contacts: [], top_companies: [] },
      activity_intelligence: { meetings: 0, emails: 0, calls: 0, tasks: 0, notes: 0, documents: 0, total: 0, recent: [] },
      kpis: { revenue: 0, pipeline: 0, win_rate: 0, response_rate: 0, follow_up_rate: 0, activities: 0, productivity: 0, forecast: 0 },
      ai_coach: [],
    }
    mockedApi.getEmployee360.mockResolvedValue(response)
    const { result } = renderHook(() => useEmployee360('e-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.getEmployee360).toHaveBeenCalledWith('e-1', 'tenant-1')
  })

  it('does not fetch when id is empty', () => {
    const { result } = renderHook(() => useEmployee360(''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useMy360', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches my 360 data', async () => {
    const response = {
      profile: { id: 'me', full_name: 'Ahmed', full_name_ar: 'أحمد', email: 'a@b.com', role: 'manager', phone: null, avatar_url: null, is_active: true, tenant_id: 't-1', created_at: '2026-01-01', team: [], manager: null },
      portfolio: { companies: [], contacts: [], pipeline: [], revenue: 0, contracts: [], projects: [] },
      calendar_intelligence: { today_count: 0, week_count: 0, month_count: 0, total_hours: 0, avg_duration_minutes: 0, unique_companies_met: 0, upcoming: [] },
      email_intelligence: { sent: 0, received: 0, replies: 0, avg_response_hours: 0, top_contacts: [], top_companies: [] },
      activity_intelligence: { meetings: 0, emails: 0, calls: 0, tasks: 0, notes: 0, documents: 0, total: 0, recent: [] },
      kpis: { revenue: 0, pipeline: 0, win_rate: 0, response_rate: 0, follow_up_rate: 0, activities: 0, productivity: 0, forecast: 0 },
      ai_coach: [],
    }
    mockedApi.getMy360.mockResolvedValue(response)
    const { result } = renderHook(() => useMy360(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.getMy360).toHaveBeenCalledWith('tenant-1')
  })
})
