"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useDebounce } from "@salesos/hooks"
import { getTenantId } from "./useTenant"
import api from "@/lib/api"
import type { SearchResultItem } from "@/lib/api"

export interface UnifiedSearchResult {
  id: string
  type: "company" | "contact" | "opportunity" | "document"
  title: string
  subtitle?: string
  href: string
  score: number
  raw: SearchResultItem
}

export interface UseUnifiedSearchOptions {
  query: string
  limit?: number
  debounceMs?: number
  enabled?: boolean
}

export interface UseUnifiedSearchReturn {
  results: UnifiedSearchResult[]
  groupedResults: Record<string, UnifiedSearchResult[]>
  loading: boolean
  error: string | null
  totalCount: number
  tookMs: number
  suggestions: string[]
}

function mapSearchResult(item: SearchResultItem): UnifiedSearchResult {
  const data = item.data || {}
  const entityType = item.type || "company"
  const typeMap: Record<string, UnifiedSearchResult["type"]> = {
    company: "company",
    contact: "contact",
    opportunity: "opportunity",
    document: "document",
  }
  const hrefMap: Record<string, (id: string) => string> = {
    company: (id) => `/companies/${id}`,
    contact: (id) => `/contacts/${id}`,
    opportunity: (id) => `/opportunities/${id}`,
    document: (id) => `/documents/${id}`,
  }
  const type = typeMap[entityType] || "company"

  let title = ""
  let subtitle = ""
  if (type === "company") {
    title = (data.name_ar as string) || (data.name_en as string) || item.id
    subtitle = data.cr_number
      ? `${data.cr_number} | ${(data.city as string) || ""}`
      : (data.city as string) || ""
  } else if (type === "contact") {
    title = (data.name as string) || item.id
    subtitle = [data.position, data.company_name].filter(Boolean).join(" · ")
  } else if (type === "opportunity") {
    title = (data.name as string) || item.id
    subtitle = data.company_name ? String(data.company_name) : ""
  } else {
    title = (data.title as string) || item.id
    subtitle = ""
  }

  return {
    id: item.id,
    type,
    title,
    subtitle,
    href: (hrefMap[type] || hrefMap.company)(item.id),
    score: item.score,
    raw: item,
  }
}

export function useUnifiedSearch({
  query,
  limit = 10,
  debounceMs = 300,
  enabled = true,
}: UseUnifiedSearchOptions): UseUnifiedSearchReturn {
  const [results, setResults] = useState<UnifiedSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [tookMs, setTookMs] = useState(0)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const abortRef = useRef<AbortController | null>(null)
  const debouncedQuery = useDebounce(query, debounceMs)

  const fetchSearch = useCallback(
    async (q: string) => {
      if (!q.trim() || !enabled) {
        setResults([])
        setTotalCount(0)
        setTookMs(0)
        setSuggestions([])
        return
      }

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setLoading(true)
      setError(null)

      try {
        const res = await api.get("/api/v1/search", {
          params: { q, limit, strategy: "hybrid" },
          headers: { "X-Tenant-Id": getTenantId() },
          signal: controller.signal,
        })
        const data = res.data
        const items: UnifiedSearchResult[] = (data.items || []).map(mapSearchResult)
        setResults(items)
        setTotalCount(data.total || items.length)
        setTookMs(data.took_ms || 0)
        setSuggestions(data.suggestions || [])
      } catch (err: unknown) {
        if (err && typeof err === "object" && "name" in err && (err as { name: string }).name === "CanceledError") return
        setError(err instanceof Error ? err.message : "Search failed")
        setResults([])
      } finally {
        setLoading(false)
      }
    },
    [limit, enabled]
  )

  useEffect(() => {
    fetchSearch(debouncedQuery)
    return () => abortRef.current?.abort()
  }, [debouncedQuery, fetchSearch])

  const groupedResults = results.reduce(
    (acc, r) => {
      if (!acc[r.type]) acc[r.type] = []
      acc[r.type].push(r)
      return acc
    },
    {} as Record<string, UnifiedSearchResult[]>
  )

  return { results, groupedResults, loading, error, totalCount, tookMs, suggestions }
}
