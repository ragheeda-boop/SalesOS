import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useLogin, useRegister, useCreateCompany, useUpdateCompany, useDeleteCompany, useAddContact } from '../mutationHooks'

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

describe('useLogin', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('stores tokens on login', async () => {
    mockedApi.post.mockResolvedValue({ data: { access_token: 'at-1', refresh_token: 'rt-1', tenant_id: 't-1' } })
    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() })

    result.current.mutate({ email: 'a@b.com', password: 'secret' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(localStorage.getItem('access_token')).toBe('at-1')
    expect(localStorage.getItem('refresh_token')).toBe('rt-1')
    expect(localStorage.getItem('tenant_id')).toBe('t-1')
  })
})

describe('useRegister', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('stores tokens on register', async () => {
    mockedApi.post.mockResolvedValue({ data: { access_token: 'at-2', refresh_token: 'rt-2', tenant_id: 't-2' } })
    const { result } = renderHook(() => useRegister(), { wrapper: createWrapper() })

    result.current.mutate({ email: 'a@b.com', password: 'secret', fullName: 'Ahmed' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(localStorage.getItem('access_token')).toBe('at-2')
  })
})

describe('useCreateCompany', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('creates a company', async () => {
    mockedApi.post.mockResolvedValue({ data: { id: 'c-1', name_ar: 'شركة' } })
    const { result } = renderHook(() => useCreateCompany(), { wrapper: createWrapper() })

    result.current.mutate({ name_ar: 'شركة', cr_number: '123456' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/v1/companies',
      { name_ar: 'شركة', cr_number: '123456' },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })
})

describe('useUpdateCompany', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('updates a company', async () => {
    mockedApi.patch.mockResolvedValue({ data: { id: 'c-1', name_ar: 'محدث' } })
    const { result } = renderHook(() => useUpdateCompany(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'c-1', name_ar: 'محدث' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.patch).toHaveBeenCalledWith(
      '/api/v1/companies/c-1',
      { name_ar: 'محدث' },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })
})

describe('useDeleteCompany', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('deletes a company', async () => {
    mockedApi.delete.mockResolvedValue({})
    const { result } = renderHook(() => useDeleteCompany(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'c-1' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.delete).toHaveBeenCalledWith(
      '/api/v1/companies/c-1',
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })
})

describe('useAddContact', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('adds a contact to company', async () => {
    mockedApi.post.mockResolvedValue({ data: { id: 'contact-1', name: 'Ali' } })
    const { result } = renderHook(() => useAddContact(), { wrapper: createWrapper() })

    result.current.mutate({ companyId: 'c-1', name: 'Ali', position: 'CEO' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/v1/companies/c-1/contacts',
      { name: 'Ali', position: 'CEO' },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })
})
