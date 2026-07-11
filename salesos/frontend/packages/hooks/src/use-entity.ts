import { useState, useEffect, useCallback } from 'react'
import { useRuntime } from './use-runtime'
import axios from 'axios'

interface UseEntityOptions {
  fields?: string[]
  cacheTtlMs?: number
}

export function useEntity<T = Record<string, unknown>>(
  entityType: string,
  entityId: string | null,
  options?: UseEntityOptions
) {
  const runtime = useRuntime()
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (!entityId) {
      setData(null)
      setLoading(false)
      return
    }
    const cacheKey = `entity:${entityType}:${entityId}`
    const cached = runtime.cache.get<T>(cacheKey)
    if (cached !== null) {
      setData(cached)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const params = options?.fields ? { fields: options.fields.join(',') } : {}
      const res = await axios.get(`/api/v1/data/${entityType}/${entityId}`, { params })
      const result = res.data as T
      runtime.cache.set(cacheKey, result, options?.cacheTtlMs)
      setData(result)
    } catch (err: any) {
      setError(err.message || 'Failed to load entity')
    } finally {
      setLoading(false)
    }
  }, [entityType, entityId, options?.fields?.join(','), options?.cacheTtlMs, runtime])

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error, refetch: fetch }
}
