import { checkPermissions, setPermissionChecker } from '../widget-permissions'

describe('widget-permissions', () => {
  beforeEach(() => {
    setPermissionChecker({ hasPermission: () => true })
  })

  it('allows access when no required permissions', () => {
    expect(checkPermissions()).toBe(true)
    expect(checkPermissions([])).toBe(true)
  })

  it('denies access when permission is not granted', () => {
    setPermissionChecker({ hasPermission: () => false })
    expect(checkPermissions(['widget.view'])).toBe(false)
  })

  it('allows access when all permissions are granted', () => {
    const checker = jest.fn().mockReturnValue(true)
    setPermissionChecker({ hasPermission: checker })
    expect(checkPermissions(['widget.view', 'widget.edit'])).toBe(true)
    expect(checker).toHaveBeenCalledTimes(2)
  })
})
