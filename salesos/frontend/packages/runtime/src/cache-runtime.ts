export interface CacheEntry<T = unknown> {
  value: T
  expiresAt: number
  createdAt: number
  stale: boolean
}

export interface CacheOptions {
  ttlMs?: number
  staleWhileRevalidateMs?: number
  maxEntries?: number
}

export class CacheRuntime {
  private cache = new Map<string, CacheEntry<unknown>>()
  private ttlMs: number
  private staleWhileRevalidateMs: number
  private maxEntries: number
  private pendingRevalidations = new Map<string, Promise<unknown>>()

  constructor(options?: CacheOptions) {
    this.ttlMs = options?.ttlMs ?? 5 * 60 * 1000
    this.staleWhileRevalidateMs = options?.staleWhileRevalidateMs ?? 60 * 1000
    this.maxEntries = options?.maxEntries ?? 500
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null
    if (Date.now() > entry.expiresAt) {
      if (Date.now() > entry.expiresAt + this.staleWhileRevalidateMs) {
        this.cache.delete(key)
        return null
      }
    }
    return entry.value as T
  }

  private getEntry<T>(key: string): { value: T | undefined; stale: boolean } {
    const entry = this.cache.get(key)
    if (!entry) return { value: undefined, stale: false }
    if (Date.now() > entry.expiresAt) {
      if (Date.now() > entry.expiresAt + this.staleWhileRevalidateMs) {
        this.cache.delete(key)
        return { value: undefined, stale: false }
      }
      return { value: entry.value as T, stale: true }
    }
    return { value: entry.value as T, stale: false }
  }

  set<T>(key: string, value: T, customTtlMs?: number): void {
    if (this.cache.size >= this.maxEntries) {
      const oldest = this.cache.entries().next()
      if (oldest.value) this.cache.delete(oldest.value[0])
    }
    this.cache.set(key, {
      value,
      expiresAt: Date.now() + (customTtlMs ?? this.ttlMs),
      createdAt: Date.now(),
      stale: false,
    })
  }

  async getOrFetch<T>(key: string, fetcher: () => Promise<T>, customTtlMs?: number): Promise<T> {
    const { value, stale } = this.getEntry<T>(key)
    if (value !== undefined && !stale) return value
    if (stale) {
      this.revalidate(key, fetcher, customTtlMs)
      return value as T
    }
    return this.fetchAndCache(key, fetcher, customTtlMs)
  }

  private async revalidate<T>(key: string, fetcher: () => Promise<T>, customTtlMs?: number): Promise<void> {
    if (this.pendingRevalidations.has(key)) return
    const promise = fetcher()
      .then((value) => {
        this.set(key, value, customTtlMs)
        this.pendingRevalidations.delete(key)
      })
      .catch(() => this.pendingRevalidations.delete(key))
    this.pendingRevalidations.set(key, promise)
  }

  private async fetchAndCache<T>(key: string, fetcher: () => Promise<T>, customTtlMs?: number): Promise<T> {
    const existing = this.pendingRevalidations.get(key)
    if (existing) return existing as Promise<T>
    const promise = fetcher()
      .then((value) => {
        this.set(key, value, customTtlMs)
        this.pendingRevalidations.delete(key)
        return value
      })
      .catch((err) => {
        this.pendingRevalidations.delete(key)
        throw err
      })
    this.pendingRevalidations.set(key, promise)
    return promise
  }

  invalidate(key: string): void {
    this.cache.delete(key)
  }

  invalidatePattern(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(pattern) || key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }

  clear(): void {
    this.cache.clear()
    this.pendingRevalidations.clear()
  }

  size(): number {
    return this.cache.size
  }

  keys(): string[] {
    return Array.from(this.cache.keys())
  }
}
