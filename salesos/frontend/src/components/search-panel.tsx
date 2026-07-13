"use client"

import { useState, useRef, useEffect } from "react"
import { Building2, Users, DollarSign, FileText, X, ArrowRight } from "lucide-react"
import { cn } from "@salesos/ui"
import Link from "next/link"
import { useUnifiedSearch, type UnifiedSearchResult } from "@/lib/hooks/useUnifiedSearch"
import { useFocusTrap } from "@/lib/hooks/useFocusTrap"

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
  const inputRef = useRef<HTMLInputElement>(null)
  const trapRef = useFocusTrap<HTMLDivElement>(open)
  const { groupedResults, loading, totalCount, tookMs, suggestions } = useUnifiedSearch({
    query,
    limit: 10,
    enabled: open,
  })

  useEffect(() => {
    if (open) {
      setQuery("")
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="بحث"
    >
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <div
        ref={trapRef}
        className="relative w-full max-w-2xl max-sm:max-w-full max-sm:mx-2 rounded-xl border border-neutral-200 bg-white shadow-2xl dark:border-neutral-700 dark:bg-neutral-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-neutral-200 px-4 dark:border-neutral-700">
          <Building2 className="h-5 w-5 text-neutral-400" aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose()
            }}
            placeholder="ابحث في الشركات، جهات الاتصال، الفرص..."
            className="h-12 flex-1 bg-transparent text-sm text-neutral-900 outline-none placeholder:text-neutral-400 dark:text-neutral-100"
            aria-label="بحث شامل"
            aria-autocomplete="list"
          />
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            aria-label="إغلاق البحث"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="max-h-96 overflow-y-auto p-2" role="list" aria-label="نتائج البحث">
          <div aria-live="polite" aria-atomic="true" className="sr-only">
            {loading
              ? "جاري البحث..."
              : totalCount > 0
                ? `${totalCount} نتيجة في ${tookMs} مللي ثانية`
                : query && !loading
                  ? "لا توجد نتائج"
                  : ""}
          </div>

          {loading && (
            <div className="flex items-center justify-center py-8" role="status">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--muhide-orange)] border-t-transparent motion-reduce:animate-none" />
              <span className="ms-2 text-sm text-neutral-500 dark:text-neutral-400">جاري البحث...</span>
            </div>
          )}

          {!loading && query && Object.keys(groupedResults).length === 0 && (
            <div className="px-3 py-8 text-center">
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                لا توجد نتائج لـ &ldquo;{query}&rdquo;
              </p>
              {suggestions.length > 0 && (
                <p className="mt-2 text-xs text-neutral-400">
                  اقتراحات: {suggestions.join("، ")}
                </p>
              )}
            </div>
          )}

          {!loading &&
            Object.entries(groupedResults).map(([type, items]) => (
              <div key={type} role="group" aria-label={typeLabels[type] || type}>
                <div className="flex items-center gap-2 px-3 py-2">
                  {typeIcons[type]}
                  <span className="text-[10px] font-medium uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    {typeLabels[type] || type}
                  </span>
                  <span className="text-[10px] text-neutral-400">({items.length})</span>
                </div>
                {items.map((item: UnifiedSearchResult) => (
                  <Link
                    key={item.id}
                    href={item.href}
                    onClick={onClose}
                    role="listitem"
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                      "hover:bg-neutral-50 dark:hover:bg-neutral-800"
                    )}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
                      {typeIcons[item.type]}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-neutral-900 dark:text-neutral-100">{item.title}</p>
                      {item.subtitle && (
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">{item.subtitle}</p>
                      )}
                    </div>
                    <ArrowRight className="h-4 w-4 text-neutral-400" aria-hidden="true" />
                  </Link>
                ))}
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
