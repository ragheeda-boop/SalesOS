import { WidgetPermissions } from '../widget-permissions'

describe('WidgetPermissions', () => {
  it('allows access when no rules defined', () => {
    const perms = new WidgetPermissions({})
    expect(perms.canView('widget-1')).toBe(true)
  })

  it('denies access when widget is not in allowed list', () => {
    const perms = new WidgetPermissions({ allowedWidgets: ['widget-1', 'widget-2'] })
    expect(perms.canView('widget-3')).toBe(false)
  })

  it('allows access when widget is in allowed list', () => {
    const perms = new WidgetPermissions({ allowedWidgets: ['widget-1'] })
    expect(perms.canView('widget-1')).toBe(true)
  })

  it('checks role-based access', () => {
    const perms = new WidgetPermissions({ roleWidgets: { admin: ['widget-1', 'widget-2'], user: ['widget-1'] } })
    expect(perms.canViewByRole('widget-2', 'admin')).toBe(true)
    expect(perms.canViewByRole('widget-2', 'user')).toBe(false)
  })
})
