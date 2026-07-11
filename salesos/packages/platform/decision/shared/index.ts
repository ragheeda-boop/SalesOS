export function generateId(prefix = 'dec'): string {
  const ts = Date.now().toString(36)
  const rand = Math.random().toString(36).substring(2, 11)
  return `${prefix}_${ts}_${rand}`
}

export function nowISO(): string {
  return new Date().toISOString()
}

export function clamp(value: number, min = 0, max = 1): number {
  return Math.max(min, Math.min(max, value))
}

export function weightedAverage(
  factors: { value: number; weight: number }[]
): number {
  const totalWeight = factors.reduce((sum, f) => sum + f.weight, 0)
  if (totalWeight === 0) return 0
  const weightedSum = factors.reduce((sum, f) => sum + f.value * f.weight, 0)
  return weightedSum / totalWeight
}

export function confidenceLabel(value: number): 'high' | 'medium' | 'low' {
  if (value >= 0.7) return 'high'
  if (value >= 0.4) return 'medium'
  return 'low'
}

export function categorizeRisk(value: number): 'critical' | 'high' | 'medium' | 'low' {
  if (value >= 0.8) return 'critical'
  if (value >= 0.6) return 'high'
  if (value >= 0.3) return 'medium'
  return 'low'
}

export function hoursAgo(isoString: string): number {
  const then = new Date(isoString).getTime()
  const now = Date.now()
  return (now - then) / (1000 * 60 * 60)
}

export function freshnessLabel(hours: number): 'fresh' | 'recent' | 'stale' | 'expired' {
  if (hours < 1) return 'fresh'
  if (hours < 24) return 'recent'
  if (hours < 168) return 'stale'
  return 'expired'
}

export function deduplicateBy<T>(
  items: T[],
  keyFn: (item: T) => string,
  keepFn?: (a: T, b: T) => T
): T[] {
  const map = new Map<string, T>()
  for (const item of items) {
    const key = keyFn(item)
    if (map.has(key)) {
      if (keepFn) {
        map.set(key, keepFn(map.get(key)!, item))
      }
    } else {
      map.set(key, item)
    }
  }
  return Array.from(map.values())
}

export function paginate<T>(items: T[], page: number, limit: number): { items: T[]; total: number; page: number; hasMore: boolean } {
  const start = (page - 1) * limit
  const paged = items.slice(start, start + limit)
  return { items: paged, total: items.length, page, hasMore: start + limit < items.length }
}
