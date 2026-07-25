"use client"

import { useState, useCallback, useMemo, useRef, useEffect } from "react"
import { useEmployeeTimeline } from "@/lib/hooks/employeeQueries"
import { Card, CardContent, Skeleton, EmptyState, Badge, Button, cn } from "@salesos/ui"
import { Clock, Filter, X, ChevronDown } from "lucide-react"
import { useTranslation } from "@/lib/i18n"
import { ErrorFallback } from "@/components/foundation/error-boundary"
import { formatRelativeTime, getActionConfig, SOURCE_OPTIONS, TYPE_OPTIONS } from "./employee-360-shared"
import type { EmployeeTimelineParams } from "@/lib/api"

export function EmployeeTimeline({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const [filters, setFilters] = useState<EmployeeTimelineParams>({ page_size: 20 })
  const [showFilters, setShowFilters] = useState(false)
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [allEvents, setAllEvents] = useState<Array<{ id: string; action: string; title: string; source_label: string; timestamp: string; actor?: string }>>([])
  const [cursorStack, setCursorStack] = useState<string[]>([])
  const listEndRef = useRef<HTMLDivElement>(null)

  const queryParams = useMemo(() => ({
    ...filters,
    source: selectedSources.length > 0 ? selectedSources : undefined,
    type: selectedTypes.length > 0 ? selectedTypes : undefined,
    from: dateFrom || undefined,
    to: dateTo || undefined,
  }), [filters, selectedSources, selectedTypes, dateFrom, dateTo])

  const { data, isLoading, isError, error, refetch } = useEmployeeTimeline(employeeId, queryParams)

  useEffect(() => {
    if (data?.events) {
      setAllEvents(data.events)
    }
  }, [data])

  const handleLoadMore = useCallback(() => {
    if (data?.next_cursor) {
      setCursorStack((prev) => [...prev, filters.cursor || ""])
      setFilters((prev) => ({ ...prev, cursor: data.next_cursor || undefined }))
    }
  }, [data, filters.cursor])

  const handleApplyFilters = useCallback(() => {
    setFilters((prev) => ({ ...prev, cursor: undefined }))
    setCursorStack([])
  }, [])

  const handleClearFilters = useCallback(() => {
    setSelectedSources([])
    setSelectedTypes([])
    setDateFrom("")
    setDateTo("")
    setFilters({ page_size: 20 })
    setCursorStack([])
  }, [])

  const handleToggleSource = useCallback((source: string) => {
    setSelectedSources((prev) => prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source])
  }, [])

  const handleToggleType = useCallback((type: string) => {
    setSelectedTypes((prev) => prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type])
  }, [])

  const hasActiveFilters = selectedSources.length > 0 || selectedTypes.length > 0 || dateFrom || dateTo

  if (isLoading && allEvents.length === 0) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 rounded-xl" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex gap-3 animate-pulse">
              <div className="h-8 w-8 rounded-full bg-[var(--bg-tertiary)]" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-3/4 rounded bg-[var(--bg-tertiary)]" />
                <div className="h-2 w-1/2 rounded bg-[var(--bg-tertiary)]" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorFallback title={t("emp360.timeline_error")} message={(error as Error)?.message} onRetry={() => refetch()} />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{t("emp360.timeline_title")}</h3>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button onClick={handleClearFilters} className="inline-flex items-center gap-1 text-xs text-[var(--muhide-orange)] hover:underline">
              <X className="h-3 w-3" /> {t("emp360.clear_filters")}
            </button>
          )}
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Filter className="h-3 w-3" />}
            onClick={() => setShowFilters(!showFilters)}
          >
            {t("emp360.filters")}
            {hasActiveFilters && <Badge variant="primary" className="ml-1 text-[10px]">{selectedSources.length + selectedTypes.length + (dateFrom ? 1 : 0) + (dateTo ? 1 : 0)}</Badge>}
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card>
          <CardContent className="py-4">
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-medium text-[var(--text-secondary)]">{t("emp360.filter_source")}</label>
                <div className="flex flex-wrap gap-1.5">
                  {SOURCE_OPTIONS.map((source) => (
                    <button
                      key={source}
                      onClick={() => handleToggleSource(source)}
                      className={cn(
                        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                        selectedSources.includes(source)
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] border border-[var(--muhide-orange)]/30"
                          : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-neutral-700 border border-transparent"
                      )}
                    >
                      {source}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-2 block text-xs font-medium text-[var(--text-secondary)]">{t("emp360.filter_type")}</label>
                <div className="flex flex-wrap gap-1.5">
                  {TYPE_OPTIONS.map((type) => (
                    <button
                      key={type}
                      onClick={() => handleToggleType(type)}
                      className={cn(
                        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                        selectedTypes.includes(type)
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] border border-[var(--muhide-orange)]/30"
                          : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-neutral-700 border border-transparent"
                      )}
                    >
                      {type.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("emp360.filter_from")}</label>
                  <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("emp360.filter_to")}</label>
                  <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs" />
                </div>
              </div>
              <Button size="sm" onClick={handleApplyFilters}>{t("emp360.apply_filters")}</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {allEvents.length === 0 && !isLoading ? (
        <div className="py-12">
          <EmptyState icon={<Clock className="h-10 w-10" />} title={t("emp360.no_timeline_events")} description={hasActiveFilters ? t("emp360.try_different_filters") : t("emp360.no_activity")} />
        </div>
      ) : (
        <div className="space-y-0">
          {allEvents.map((event, idx) => {
            const config = getActionConfig(event.action)
            const Icon = config.icon
            return (
              <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                {idx < allEvents.length - 1 && (
                  <div className="absolute right-[15px] top-10 bottom-0 w-px bg-[var(--bg-tertiary)]" />
                )}
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", config.color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{event.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                    <Badge variant="default" className="mr-1 text-[10px]">{event.source_label}</Badge>
                    {event.actor && <span className="mr-1">· {event.actor}</span>}
                    <span>· {formatRelativeTime(event.timestamp)}</span>
                  </p>
                </div>
              </div>
            )
          })}
          <div ref={listEndRef} />
        </div>
      )}

      {data?.has_next && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" size="sm" onClick={handleLoadMore} leftIcon={<ChevronDown className="h-4 w-4" />}>
            {t("emp360.load_more")}
          </Button>
        </div>
      )}

      {data && !data.has_next && allEvents.length > 0 && (
        <p className="text-center text-xs text-[var(--text-disabled)] pt-2">{t("emp360.all_events_loaded")}</p>
      )}
    </div>
  )
}
