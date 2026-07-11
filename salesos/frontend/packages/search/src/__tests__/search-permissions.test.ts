import { canSearch, canViewResult, setSearchPermissionChecker, filterResultsByPermission } from '../search-permissions'

describe('search-permissions', () => {
  it('defaults to all allowed', () => {
    expect(canSearch('company')).toBe(true)
    expect(canViewResult('c1', 'company')).toBe(true)
  })

  it('respects setSearchPermissionChecker', () => {
    setSearchPermissionChecker({
      canSearch: (type) => type === 'company',
      canViewResult: () => false,
    })
    expect(canSearch('company')).toBe(true)
    expect(canSearch('person')).toBe(false)
    expect(canViewResult('c1', 'company')).toBe(false)
  })

  it('filterResultsByPermission filters results', () => {
    setSearchPermissionChecker({
      canSearch: () => true,
      canViewResult: (id) => id !== 'blocked',
    })
    const results = filterResultsByPermission([
      { id: 'a', entityType: 'company' },
      { id: 'blocked', entityType: 'company' },
    ])
    expect(results).toHaveLength(1)
  })
})
