export interface PermissionChecker {
  hasPermission(permission: string): boolean
}

let checker: PermissionChecker = { hasPermission: () => true }

export function setPermissionChecker(c: PermissionChecker) {
  checker = c
}

export function checkPermissions(required?: string[]): boolean {
  if (!required || required.length === 0) return true
  return required.every((p) => checker.hasPermission(p))
}
