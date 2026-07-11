import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useCompany360 } from '../company360Queries'

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

describe('useCompany360', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches company 360 data', async () => {
    const company360 = {
      company: { id: 'c-1', name_ar: 'شركة', cr_number: '123456', status: 'active', city: null, region: null, phone: null, email: null, confidence_score: 0.9, created_at: '2026-01-01', updated_at: '2026-07-10', branches: [], licenses: [], contacts: [] },
      overview: { total_contacts: 5, total_opportunities: 2, total_revenue: 500000, active_contracts: 1, pending_tasks: 3, upcoming_meetings: 1, last_activity: '2026-07-10', signal_count: 10, contacts_page: 1, contacts_total: 5, opportunities_page: 1, opportunities_total: 2, timeline_page: 1, timeline_total: 20 },
      organization: { branches: [], departments: ['IT'], employees_count: 50, legal_form: 'LLC', incorporation_date: '2020-01-01' },
      contacts: [], assigned_employees: [], opportunities: [], contracts: [], invoices: [], timeline: [], documents: [], emails: [], meetings: [], tasks: [], signals: { items: [], total: 0 }, branches: [], licenses: [],
      enrichment: { sources: ['cr'], is_golden_record: false, confidence_score: 0.8, last_enriched_at: '2026-07-10' },
    }
    mockedApi.getCompany360.mockResolvedValue(company360)
    const { result } = renderHook(() => useCompany360('c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(company360)
    expect(mockedApi.getCompany360).toHaveBeenCalledWith('c-1', 'tenant-1')
  })

  it('does not fetch when id is empty', () => {
    const { result } = renderHook(() => useCompany360(''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})
