import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'
import axios from 'axios'
import type { UISchema } from '@salesos/renderer'

export function useSchema(entityType: string, entityId: string) {
  const runtime = useRuntime()
  const [schema, setSchema] = useState<UISchema | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const cacheKey = `schema:${entityType}:${entityId}`
    const cached = runtime.cache.get<UISchema>(cacheKey)
    if (cached.value) {
      setSchema(cached.value)
      setLoading(false)
      if (!cached.stale) return
    }

    setLoading(true)
    axios
      .get(`/api/v1/schema/viewer/${entityType}/${entityId}`)
      .then((res) => {
        if (cancelled) return
        const data = res.data as UISchema
        setSchema(data)
        runtime.cache.set(cacheKey, data)
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message || 'Failed to load schema')
        setLoading(false)
      })

    return () => { cancelled = true }
  }, [entityType, entityId, runtime])

  return { schema, loading, error, refetch: () => { runtime.cache.invalidate(`schema:${entityType}:${entityId}`) } }
}
