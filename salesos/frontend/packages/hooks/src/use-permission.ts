import { useRuntime } from './use-runtime'

export function usePermission(permission: string): boolean {
  const runtime = useRuntime()
  return runtime.session.hasPermission(permission)
}

export function useAnyPermission(permissions: string[]): boolean {
  const runtime = useRuntime()
  return runtime.session.hasAnyPermission(permissions)
}

export function useAllPermissions(permissions: string[]): boolean {
  const runtime = useRuntime()
  return runtime.session.hasAllPermissions(permissions)
}
