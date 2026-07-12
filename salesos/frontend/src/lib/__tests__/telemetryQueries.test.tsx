import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('@/lib/hooks/useTenant')

import api from '@/lib/api'
import { getTenantId } from '@/lib/hooks/useTenant'
import {
  useTelemetryOverview, useFeatureAdoption, useSearchSuccess,
  useNBAAcceptance, useActiveUsers, telemetryKeys,
} from '@/lib/telemetryQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

beforeEach(() => {
  mockedGetTenantId.mockReturnValue('tenant-1')
})

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('telemetryKeys', () => {
  it('generates consistent query keys', () => {
    expect(telemetryKeys.all).toEqual(['telemetry'])
    expect(telemetryKeys.overview()).toEqual(['telemetry', 'overview'])
    expect(telemetryKeys.featureAdoption()).toEqual(['telemetry', 'feature-adoption'])
    expect(telemetryKeys.activeUsers()).toEqual(['telemetry', 'active-users'])
  })
})

describe('useTelemetryOverview', () => {
  it('fetches telemetry overview', async () => {
    mockedApi.get.mockResolvedValue({ data: { avg_adoption_pct: 65, active_users: { dau: 10, wau: 50, mau: 200, period_days: 30 } } })
    const { result } = renderHook(() => useTelemetryOverview(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.avg_adoption_pct).toBe(65)
  })
})

describe('useFeatureAdoption', () => {
  it('fetches feature adoption data', async () => {
    mockedApi.get.mockResolvedValue({ data: [{ feature: 'search', label: 'Search', user_count: 80, total_users: 100, adoption_pct: 80 }] })
    const { result } = renderHook(() => useFeatureAdoption(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data![0].feature).toBe('search')
  })
})

describe('useSearchSuccess', () => {
  it('fetches search success data', async () => {
    mockedApi.get.mockResolvedValue({ data: { total_searches: 1000, searches_with_action: 600, success_rate: 0.6 } })
    const { result } = renderHook(() => useSearchSuccess(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.success_rate).toBe(0.6)
  })
})

describe('useNBAAcceptance', () => {
  it('fetches NBA acceptance data', async () => {
    mockedApi.get.mockResolvedValue({ data: { nba_views: 200, nba_accepts: 80, nba_rejects: 20, acceptance_rate: 0.4 } })
    const { result } = renderHook(() => useNBAAcceptance(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.acceptance_rate).toBe(0.4)
  })
})

describe('useActiveUsers', () => {
  it('fetches active user counts', async () => {
    mockedApi.get.mockResolvedValue({ data: { dau: 25, wau: 120, mau: 450, period_days: 30 } })
    const { result } = renderHook(() => useActiveUsers(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.dau).toBe(25)
  })
})
