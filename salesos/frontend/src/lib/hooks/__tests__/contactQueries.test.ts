import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('../useTenant')

import * as api from '@/lib/api'
import { getTenantId } from '../useTenant'
import { useContactSearch, useContact, useCreateContact, useUpdateContact, useDeleteContact } from '../contactQueries'

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

describe('useContactSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('searches contacts', async () => {
    const response = { total: 1, page: 1, page_size: 10, items: [{ id: 'c-1', name: 'Ali', email: 'a@b.com', phone: null, position: 'CEO' }] }
    mockedApi.searchContacts.mockResolvedValue(response)
    const { result } = renderHook(() => useContactSearch({ q: 'Ali' }), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(response)
    expect(mockedApi.searchContacts).toHaveBeenCalledWith({ q: 'Ali' }, 'tenant-1')
  })
})

describe('useContact', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches a contact', async () => {
    const contact = { id: 'c-1', name: 'Ali', email: 'a@b.com', phone: null, position: 'CEO' }
    mockedApi.getContact.mockResolvedValue(contact)
    const { result } = renderHook(() => useContact('c-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(contact)
  })
})

describe('useCreateContact', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('creates a contact', async () => {
    const created = { id: 'c-2', name: 'Mohammed', email: 'm@b.com', phone: null, position: 'CTO' }
    mockedApi.createContact.mockResolvedValue(created)
    const { result } = renderHook(() => useCreateContact(), { wrapper: createWrapper() })

    result.current.mutate({ name: 'Mohammed', email: 'm@b.com' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.createContact).toHaveBeenCalledWith({ name: 'Mohammed', email: 'm@b.com' }, 'tenant-1')
  })
})

describe('useUpdateContact', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('updates a contact', async () => {
    const updated = { id: 'c-1', name: 'Ali Updated', email: 'a@b.com', phone: null, position: 'CEO' }
    mockedApi.updateContact.mockResolvedValue(updated)
    const { result } = renderHook(() => useUpdateContact(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'c-1', name: 'Ali Updated' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.updateContact).toHaveBeenCalledWith('c-1', { name: 'Ali Updated' }, 'tenant-1')
  })
})

describe('useDeleteContact', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('deletes a contact', async () => {
    mockedApi.deleteContact.mockResolvedValue()
    const { result } = renderHook(() => useDeleteContact(), { wrapper: createWrapper() })

    result.current.mutate({ id: 'c-1' })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockedApi.deleteContact).toHaveBeenCalledWith('c-1', 'tenant-1')
  })
})
