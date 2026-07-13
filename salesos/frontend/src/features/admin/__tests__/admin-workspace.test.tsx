import { render, screen } from '@testing-library/react'

jest.mock('@/lib/hooks/adminQueries', () => ({
  useAdminTenants: () => ({ data: [], isLoading: false }),
  useAdminPlans: () => ({ data: [], isLoading: false }),
  useAdminUsers: () => ({ data: [], isLoading: false }),
  useAdminDetailedHealth: () => ({ data: null, isLoading: false }),
  useAdminLicenses: () => ({ data: [], isLoading: false }),
  useAdminFeatureFlags: () => ({ data: [], isLoading: false }),
  useAdminFlagTenants: () => ({ data: [], isLoading: false }),
  useAdminJobs: () => ({ data: [], isLoading: false }),
  useAdminJobDetail: () => ({ data: null, isLoading: false }),
  useAdminAICosts: () => ({ data: [], isLoading: false }),
  useAdminAICostSummary: () => ({ data: null, isLoading: false }),
  useAdminAIUsage: () => ({ data: null, isLoading: false }),
  useAdminHealthHistory: () => ({ data: [], isLoading: false }),
  useCreateAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDeleteAdminTenant: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminPlan: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateAdminPlan: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminLicense: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useDeactivateAdminUser: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useCreateAdminFeatureFlag: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useToggleAdminFlagForTenant: () => ({ mutate: jest.fn(), isPending: false }),
  useRetryAdminJob: () => ({ mutateAsync: jest.fn(), isPending: false }),
}))

import { AdminWorkspace } from '../AdminWorkspace'

describe('AdminWorkspace', () => {
  it('renders overview with quick actions', () => {
    render(<AdminWorkspace />)
    expect(screen.getByText('لوحة الإدارة')).toBeInTheDocument()
    expect(screen.getByText('إجراءات سريعة')).toBeInTheDocument()
  })

  it('renders sidebar navigation tabs', () => {
    render(<AdminWorkspace />)
    expect(screen.getByText('الرئيسية')).toBeInTheDocument()
    expect(screen.getByText('العملاء')).toBeInTheDocument()
    expect(screen.getByText('الباقات والتراخيص')).toBeInTheDocument()
    const usersInSidebar = screen.getAllByText('المستخدمين')
    expect(usersInSidebar.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('الميزات')).toBeInTheDocument()
    expect(screen.getByText('الوظائف')).toBeInTheDocument()
    expect(screen.getByText('تكاليف AI')).toBeInTheDocument()
    const healthItems = screen.getAllByText('صحة النظام')
    expect(healthItems.length).toBeGreaterThanOrEqual(1)
  })
})
