"use client"

import { useState, useCallback } from "react"
import { AuditLogView } from "./AuditLogView"
import { useAdminAuditLogs } from "@/lib/hooks/adminQueries"
import type { AuditLogFilters } from "./types"

export function AuditLogWidget() {
  const [filters, setFilters] = useState<AuditLogFilters>({
    dateFrom: undefined,
    dateTo: undefined,
    userId: undefined,
    actionType: undefined,
    resource: undefined,
    search: undefined,
    page: 1,
    pageSize: 20,
  })

  const { data, isLoading, refetch } = useAdminAuditLogs({
    page: filters.page,
    page_size: filters.pageSize,
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
    user_id: filters.userId,
    action_type: filters.actionType,
    resource: filters.resource,
    search: filters.search,
  })

  const handleFilterChange = useCallback((partial: Partial<AuditLogFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }))
  }, [])

  const handleExport = useCallback(() => {
    const params = new URLSearchParams()
    if (filters.dateFrom) params.set("date_from", filters.dateFrom)
    if (filters.dateTo) params.set("date_to", filters.dateTo)
    if (filters.actionType) params.set("action_type", filters.actionType)
    if (filters.resource) params.set("resource", filters.resource)
    if (filters.search) params.set("search", filters.search)
    window.open(`/api/v1/admin/audit/logs/export?${params.toString()}`, "_blank")
  }, [filters])

  return (
    <AuditLogView
      items={data?.items ?? []}
      total={data?.total ?? 0}
      loading={isLoading}
      filters={filters}
      onFilterChange={handleFilterChange}
      onExport={handleExport}
      onRefresh={refetch}
    />
  )
}
