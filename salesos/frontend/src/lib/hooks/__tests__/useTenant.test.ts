import { renderHook } from '@testing-library/react'
import { getTenantId, useTenant } from '../useTenant'

describe('getTenantId', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns stored tenant_id when present', () => {
    localStorage.setItem('tenant_id', 'tenant-123')
    expect(getTenantId()).toBe('tenant-123')
  })

  it('extracts tenant_id from JWT when no stored tenant_id', () => {
    const payload = btoa(JSON.stringify({ tenant_id: 'jwt-tenant' }))
    const token = `header.${payload}.signature`
    localStorage.setItem('access_token', token)
    expect(getTenantId()).toBe('jwt-tenant')
  })

  it('returns "default" when no tenant info available', () => {
    expect(getTenantId()).toBe('default')
  })

  it('returns "default" for malformed JWT', () => {
    localStorage.setItem('access_token', 'not-a-jwt')
    expect(getTenantId()).toBe('default')
  })
})

describe('useTenant', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns tenantId from hook', () => {
    localStorage.setItem('tenant_id', 'tenant-456')
    const { result } = renderHook(() => useTenant())
    expect(result.current.tenantId).toBe('tenant-456')
  })
})
