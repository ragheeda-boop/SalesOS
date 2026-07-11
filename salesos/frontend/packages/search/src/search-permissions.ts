export interface SearchPermissionChecker {
  canSearch(entityType: string): boolean
  canViewResult(resultId: string, entityType: string): boolean
}

let checker: SearchPermissionChecker = {
  canSearch: () => true,
  canViewResult: () => true,
}

export function setSearchPermissionChecker(c: SearchPermissionChecker) {
  checker = c
}

export function canSearch(entityType: string): boolean {
  return checker.canSearch(entityType)
}

export function canViewResult(resultId: string, entityType: string): boolean {
  return checker.canViewResult(resultId, entityType)
}

export function filterResultsByPermission<T extends { id: string; entityType: string }>(results: T[]): T[] {
  return results.filter((r) => canViewResult(r.id, r.entityType))
}
