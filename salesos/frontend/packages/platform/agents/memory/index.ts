import type { MemoryEntry, MemoryType } from '../contracts'

const entries = new Map<string, MemoryEntry[]>()
const timers = new Map<string, ReturnType<typeof setTimeout>>()

function entryId(): string {
  return crypto.randomUUID()
}

function now(): string {
  return new Date().toISOString()
}

function storeKey(agentId: string, key: string): string {
  return `${agentId}::${key}`
}

function isExpired(entry: MemoryEntry): boolean {
  if (entry.ttl <= 0) return false
  const elapsed = Date.now() - new Date(entry.timestamp).getTime()
  return elapsed >= entry.ttl
}

function scheduleEviction(agentId: string, key: string, ttl: number): void {
  if (ttl <= 0) return
  const timerKey = storeKey(agentId, key)
  const existing = timers.get(timerKey)
  if (existing) clearTimeout(existing)

  const timer = setTimeout(() => {
    forget(agentId, key)
    timers.delete(timerKey)
  }, ttl)
  timers.set(timerKey, timer)
}

export function store(
  agentId: string,
  key: string,
  value: unknown,
  ttl: number = 3600000,
  type: MemoryType = 'working',
): void {
  const agentEntries = entries.get(agentId) ?? []
  const existing = agentEntries.find(e => e.key === key)
  if (existing) {
    existing.value = value
    existing.ttl = ttl
    existing.timestamp = now()
  } else {
    agentEntries.push({
      id: entryId(),
      agentId,
      type,
      key,
      value,
      ttl,
      timestamp: now(),
    })
  }
  entries.set(agentId, agentEntries)
  scheduleEviction(agentId, key, ttl)
}

export function recall(agentId: string, key: string): unknown | undefined {
  const agentEntries = entries.get(agentId)
  if (!agentEntries) return undefined

  const entry = agentEntries.find(e => e.key === key)
  if (!entry) return undefined

  if (isExpired(entry)) {
    forget(agentId, key)
    return undefined
  }

  return entry.value
}

export function forget(agentId: string, key: string): void {
  const agentEntries = entries.get(agentId)
  if (!agentEntries) return

  const filtered = agentEntries.filter(e => e.key !== key)
  entries.set(agentId, filtered)

  const timerKey = storeKey(agentId, key)
  const timer = timers.get(timerKey)
  if (timer) {
    clearTimeout(timer)
    timers.delete(timerKey)
  }
}

export function clear(agentId: string): void {
  entries.delete(agentId)
  for (const [key, _timer] of timers) {
    if (key.startsWith(`${agentId}::`)) {
      clearTimeout(_timer)
      timers.delete(key)
    }
  }
}

export function getContext(agentId: string): Record<string, unknown> {
  const agentEntries = entries.get(agentId)
  if (!agentEntries) return {}

  const result: Record<string, unknown> = {}
  const now = Date.now()

  for (const entry of agentEntries) {
    if (entry.ttl > 0 && (now - new Date(entry.timestamp).getTime()) >= entry.ttl) continue
    result[entry.key] = entry.value
  }

  return result
}
