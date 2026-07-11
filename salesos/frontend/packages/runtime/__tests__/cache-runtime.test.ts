import { CacheRuntime } from '../src/cache-runtime'

describe('CacheRuntime', () => {
  let cache: CacheRuntime

  beforeEach(() => {
    cache = new CacheRuntime()
  })

  it('stores and retrieves values', () => {
    cache.set('key1', 'value1')
    expect(cache.get('key1')).toBe('value1')
  })

  it('returns null for missing keys', () => {
    expect(cache.get('missing')).toBeNull()
  })

  it('respects TTL', () => {
    jest.useFakeTimers()
    cache.set('key', 'val', 100)
    jest.advanceTimersByTime(150 + 61_000)
    expect(cache.get('key')).toBeNull()
    jest.useRealTimers()
  })

  it('evicts LRU entries when at capacity', () => {
    const smallCache = new CacheRuntime({ maxEntries: 2 })
    smallCache.set('a', 1)
    smallCache.set('b', 2)
    smallCache.set('c', 3)
    expect(smallCache.get('a')).toBeNull()
    expect(smallCache.get('b')).toBe(2)
    expect(smallCache.get('c')).toBe(3)
  })

  it('invalidates specific keys', () => {
    cache.set('a', 1)
    cache.set('b', 2)
    cache.invalidate('a')
    expect(cache.get('a')).toBeNull()
    expect(cache.get('b')).toBe(2)
  })

  it('clears all entries', () => {
    cache.set('a', 1)
    cache.set('b', 2)
    cache.clear()
    expect(cache.get('a')).toBeNull()
    expect(cache.get('b')).toBeNull()
  })

  it('deduplicates pending requests', async () => {
    let callCount = 0
    const fetcher = async (k: string) => {
      callCount++
      return `fetched-${k}`
    }

    const [r1, r2] = await Promise.all([
      cache.getOrFetch('x', () => fetcher('x')),
      cache.getOrFetch('x', () => fetcher('x')),
    ])

    expect(r1).toBe('fetched-x')
    expect(r2).toBe('fetched-x')
    expect(callCount).toBe(1)
  })
})
