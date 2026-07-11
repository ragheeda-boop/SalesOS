import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

jest.mock('@/lib/api', () => ({
  listAdminTenants: jest.fn().mockResolvedValue([{ id: '1', name: 'Test Tenant', slug: 'test', plan: 'growth', is_active: true, user_count: 5, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', domain: null }]),
  listAdminPlans: jest.fn().mockResolvedValue([{ id: '1', name: 'Growth', tier: 'growth', price_monthly: 999, features: [] }]),
  listAdminUsers: jest.fn().mockResolvedValue([{ id: '1', email: 'test@test.com', full_name: 'Test', role: 'admin', is_active: true, tenant_id: '1', tenant_name: 'Test', created_at: '2026-01-01T00:00:00Z', last_login_at: null }]),
  getAdminDetailedHealth: jest.fn().mockResolvedValue({ overall_status: 'healthy', uptime_seconds: 86400, components: [] }),
  getAdminHealthHistory: jest.fn().mockResolvedValue([]),
  listAdminFeatureFlags: jest.fn().mockResolvedValue([]),
  listAdminJobs: jest.fn().mockResolvedValue([]),
  listAdminAICosts: jest.fn().mockResolvedValue([]),
  getAdminAICostSummary: jest.fn().mockResolvedValue({ total_cost: 0, total_tokens: 0, by_model: [], by_tenant: [], by_operation: [] }),
  getAdminAIUsage: jest.fn().mockResolvedValue({ total_prompt_tokens: 0, total_completion_tokens: 0, total_tokens: 0, by_model: [], by_tenant: [] }),
  listAdminLicenses: jest.fn().mockResolvedValue([]),
  getAdminTenant: jest.fn().mockResolvedValue({ id: '1', name: 'Test', slug: 'test', plan: 'free', is_active: true, settings: {}, features: {}, user_count: 0, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', subscription_ends_at: null }),
  getAdminTenantUsage: jest.fn().mockResolvedValue({ tenant_id: '1', tenant_name: 'Test', api_calls: 100, storage_mb: 50, active_users: 3, total_users: 5, period_start: '2026-01-01T00:00:00Z', period_end: '2026-01-31T00:00:00Z' }),
  listAdminInvoices: jest.fn().mockResolvedValue([]),
  listAdminTransactions: jest.fn().mockResolvedValue([]),
  createAdminTenant: jest.fn(),
  updateAdminTenant: jest.fn(),
  deleteAdminTenant: jest.fn(),
  createAdminPlan: jest.fn(),
  updateAdminPlan: jest.fn(),
  createAdminLicense: jest.fn(),
  updateAdminUser: jest.fn(),
  deactivateAdminUser: jest.fn(),
  createAdminFeatureFlag: jest.fn(),
  updateAdminFeatureFlag: jest.fn(),
  getAdminFlagTenants: jest.fn().mockResolvedValue([]),
  toggleAdminFlagForTenant: jest.fn(),
  retryAdminJob: jest.fn(),
  getAdminJob: jest.fn(),
}))

import { useAdminTenants, useAdminPlans, useAdminUsers, useAdminDetailedHealth } from '@/lib/hooks/adminQueries'

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  )
}

describe('Admin Query Hooks', () => {
  it('useAdminTenants fetches tenants', async () => {
    const { result } = renderHook(() => useAdminTenants(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].name).toBe('Test Tenant')
  })

  it('useAdminPlans fetches plans', async () => {
    const { result } = renderHook(() => useAdminPlans(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data![0].name).toBe('Growth')
  })

  it('useAdminUsers fetches users', async () => {
    const { result } = renderHook(() => useAdminUsers(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data![0].email).toBe('test@test.com')
  })

  it('useAdminDetailedHealth fetches health', async () => {
    const { result } = renderHook(() => useAdminDetailedHealth(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data!.overall_status).toBe('healthy')
  })
})
