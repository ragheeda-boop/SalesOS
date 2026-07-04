"use client"

import { useState, useRef, useEffect } from "react"
import { Search, Building2, Users, DollarSign, FileText, X, ArrowRight } from "lucide-react"
import { cn } from "@salesos/ui"
import { useDebounce } from "@salesos/hooks"
import Link from "next/link"
import api from "@/lib/api"

interface SearchResult {
  id: string
  type: "company" | "contact" | "opportunity" | "document"
  title: string
  subtitle?: string
  href: string
}

interface SearchPanelProps {
  open: boolean
  onClose: () => void
}

const typeIcons: Record<string, React.ReactNode> = {
  company: <Building2 className="h-4 w-4" />,
  contact: <Users className="h-4 w-4" />,
  opportunity: <DollarSign className="h-4 w-4" />,
  document: <FileText className="h-4 w-4" />,
}

const typeLabels: Record<string, string> = {
  company: "شركة",
  contact: "جهة اتصال",
  opportunity: "فرصة",
  document: "مستند",
}

export function SearchPanel({ open, onClose }: SearchPanelProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const debouncedQuery = useDebounce(query, 300)

  useEffect(() => {
    if (open) {
      setQuery("")
      setResults([])
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([])
      return
    }
    setLoading(true)
    api
      .get("/api/v1/search", {
        params: { q: debouncedQuery, limit: 10, strategy: "hybrid" },
      })
      .then((res) => {
        const data = res.data
        const items: SearchResult[] = (data.items || []).map((item: any) => ({
          id: item.id,
          type: "company",
          title: item.data?.name_ar || item.data?.name_en || item.id,
          subtitle: item.data?.cr_number
            ? `${item.data.cr_number} | ${item.data.city || ""}`
            : item.data?.city || "",
          href: `/companies/${item.id}`,
        }))
        setResults(items)
      })
      .catch(() => setResults([]))
      .finally(() => setLoading(false))
  }, [debouncedQuery])

  if (!open) return null

  const groupedResults = results.reduce(
    (acc, r) => {
      if (!acc[r.type]) acc[r.type] = []
      acc[r.type].push(r)
      return acc
    },
    {} as Record<string, SearchResult[]>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/50" />
      <div
        className="relative w-full max-w-2xl rounded-xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-gray-200 px-4 dark:border-gray-700">
          <Search className="h-5 w-5 text-gray-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ابحث في الشركات، جهات الاتصال، الفرص..."
            className="h-12 flex-1 bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-gray-100"
          />
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="max-h-96 overflow-y-auto p-2">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            </div>
          )}
          {!loading && query && results.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
              لا توجد نتائج لـ &ldquo;{query}&rdquo;
            </p>
          )}
          {!loading &&
            Object.entries(groupedResults).map(([type, items]) => (
              <div key={type}>
                <div className="flex items-center gap-2 px-3 py-2">
                  {typeIcons[type]}
                  <span className="text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    {typeLabels[type] || type}
                  </span>
                  <span className="text-[10px] text-gray-400">({items.length})</span>
                </div>
                {items.map((item) => (
                  <Link
                    key={item.id}
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                      "hover:bg-gray-50 dark:hover:bg-gray-800"
                    )}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                      {typeIcons[item.type]}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                      {item.subtitle && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">{item.subtitle}</p>
                      )}
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400" />
                  </Link>
                ))}
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
