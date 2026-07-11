import { useState, useCallback } from 'react'
import { useRuntime } from './use-runtime'

export function useCache<T = unknown>(key: string, fetcher?: () => Promise<T>) {
  const runtime = useRuntime()
  const [loading, setLoading] = useState(false)

  const get = useCallback((): T | null => {
    const result = runtime.cache.get<T>(key)
    return result ?? null
  }, [key, runtime])

  const set = useCallback((value: T) => {
    runtime.cache.set(key, value)
  }, [key, runtime])

  const refresh = useCallback(async () => {
    if (!fetcher) return
    setLoading(true)
    try {
      const value = await fetcher()
      runtime.cache.set(key, value)
      return value
    } finally {
      setLoading(false)
    }
  }, [key, fetcher, runtime])

  const invalidate = useCallback(() => {
    runtime.cache.invalidate(key)
  }, [key, runtime])

  return { get, set, refresh, invalidate, loading }
}
