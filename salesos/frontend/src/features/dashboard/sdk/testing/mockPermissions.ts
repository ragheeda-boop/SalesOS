import { setPermissionChecker } from '../widget-permissions'

export function mockPermissions(granted: boolean) {
  setPermissionChecker({
    hasPermission: () => granted,
  })
}

export function mockPermissionsAll() {
  setPermissionChecker({
    hasPermission: () => true,
  })
}

export function mockPermissionsNone() {
  setPermissionChecker({
    hasPermission: () => false,
  })
}
