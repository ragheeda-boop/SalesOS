"use client"

import { useState } from "react"
import { Input, Button, Badge, Card, cn, Spinner } from "@salesos/ui"
import { Search, Download, ChevronLeft, ChevronRight, FileText, Filter } from "lucide-react"
import type { AuditLogViewProps } from "./types"
import { ACTION_TYPE_LABELS, RESOURCE_LABELS } from "./types"

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("ar-SA", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    })
  } catch {
    return iso
  }
}

export function AuditLogView({ items, total, loading, filters, onFilterChange, onExport, onRefresh }: AuditLogViewProps) {
  const [showFilters, setShowFilters] = useState(false)

  const totalPages = Math.max(1, Math.ceil(total / filters.pageSize))

  return (
    <div className="space-y-4" role="region" aria-label="سجل التدقيق">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-bold">سجل التدقيق</h2>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowFilters(!showFilters)} className="gap-1">
            <Filter className="h-4 w-4" />
            {showFilters ? "إخفاء الفلتر" : "فلتر"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            تحديث
          </Button>
          <Button variant="outline" size="sm" onClick={onExport} className="gap-1">
            <Download className="h-4 w-4" />
            تصدير CSV
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card className="p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">من تاريخ</label>
              <input
                type="date"
                value={filters.dateFrom || ""}
                onChange={(e) => onFilterChange({ dateFrom: e.target.value || undefined })}
                className="w-full border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">إلى تاريخ</label>
              <input
                type="date"
                value={filters.dateTo || ""}
                onChange={(e) => onFilterChange({ dateTo: e.target.value || undefined })}
                className="w-full border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div>
              <label htmlFor="filter-action-type" className="block text-xs font-medium mb-1">نوع الإجراء</label>
              <select
                id="filter-action-type"
                aria-label="نوع الإجراء"
                value={filters.actionType || ""}
                onChange={(e) => onFilterChange({ actionType: e.target.value || undefined })}
                className="w-full border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
              >
                <option value="">الكل</option>
                {Object.entries(ACTION_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="filter-resource" className="block text-xs font-medium mb-1">المورد</label>
              <select
                id="filter-resource"
                aria-label="المورد"
                value={filters.resource || ""}
                onChange={(e) => onFilterChange({ resource: e.target.value || undefined })}
                className="w-full border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
              >
                <option value="">الكل</option>
                {Object.entries(RESOURCE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="relative max-w-sm">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
            <Input
              placeholder="بحث في السجل..."
              value={filters.search || ""}
              onChange={(e) => onFilterChange({ search: e.target.value || undefined, page: 1 })}
              className="pr-9"
            />
          </div>
        </Card>
      )}

      {loading ? (
        <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
      ) : !items.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا توجد سجلات تدقيق</p>
          <p className="text-xs mt-1">لم يتم تسجيل أي أحداث بعد</p>
        </Card>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm responsive-table">
              <thead>
                <tr className="border-b dark:border-neutral-700 text-right">
                  <th className="p-2 font-medium">التاريخ</th>
                  <th className="p-2 font-medium">المستخدم</th>
                  <th className="p-2 font-medium">الإجراء</th>
                  <th className="p-2 font-medium">المورد</th>
                  <th className="p-2 font-medium">التفاصيل</th>
                  <th className="p-2 font-medium">IP</th>
                </tr>
              </thead>
              <tbody>
                {items.map((entry) => (
                  <tr key={entry.id} className="border-b dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                    <td className="p-2 text-xs text-neutral-500 font-mono" data-label="التاريخ">
                      {formatDateTime(entry.created_at)}
                    </td>
                    <td className="p-2" data-label="المستخدم">
                      <div className="text-sm font-medium">{entry.actor_name}</div>
                      <div className="text-xs text-neutral-500">{entry.actor_email}</div>
                    </td>
                    <td className="p-2" data-label="الإجراء">
                      <Badge variant="default" className="font-mono text-[10px]">
                        {ACTION_TYPE_LABELS[entry.action_type] || entry.action_type}
                      </Badge>
                    </td>
                    <td className="p-2" data-label="المورد">
                      <div className="text-xs">
                        <span className="font-medium">{RESOURCE_LABELS[entry.resource_type] || entry.resource_type}</span>
                        <span className="text-neutral-500 mr-1">{entry.resource}</span>
                      </div>
                    </td>
                    <td className="p-2 text-xs text-neutral-600 max-w-[200px] truncate" data-label="التفاصيل">
                      {entry.details ? JSON.stringify(entry.details).slice(0, 80) : "-"}
                    </td>
                    <td className="p-2 text-xs text-neutral-500 font-mono" data-label="IP">
                      {entry.ip_address || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-neutral-500">
            <span>
              {total > 0 ? `${(filters.page - 1) * filters.pageSize + 1}-${Math.min(filters.page * filters.pageSize, total)} من ${total}` : "0 نتيجة"}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                aria-label="الصفحة السابقة"
                disabled={filters.page <= 1}
                onClick={() => onFilterChange({ page: filters.page - 1 })}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <span className="font-medium">{filters.page} / {totalPages}</span>
              <Button
                variant="ghost"
                size="sm"
                aria-label="الصفحة التالية"
                disabled={filters.page >= totalPages}
                onClick={() => onFilterChange({ page: filters.page + 1 })}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
