"use client"

import { useState, useCallback } from"react"
import Link from"next/link"
import { useRouter, useSearchParams } from"next/navigation"
import { useEmployeeSearch, useBulkEditEmployees, useBulkDeleteEmployees, useEmployeeSignals, useEmployeeScore } from"@/lib/hooks/employeeQueries"
import { useDebounce } from"@salesos/hooks"
import { DataTable, Checkbox, Input, Badge, Button, Select, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, useToast, Skeleton, EmptyState } from"@salesos/ui"
import { Search, Plus, User, ChevronLeft, ChevronRight, Loader2, Download, Edit3, Trash2, X, Activity, Brain, TrendingUp, TrendingDown, Minus, Signal, BarChart3, PieChart } from"lucide-react"
import { ErrorFallback } from"@/components/foundation/error-boundary"
import { useTranslation } from"@/lib/i18n"
import { ScoreBadge } from"@/components/employee-360/employee-360-shared"
import type { ColumnDef } from"@tanstack/react-table"
import type { EmployeeListItem } from"@/lib/api"

const DEPARTMENT_OPTIONS = [
 { label:"All", value:"" },
 { label:"Sales", value:"sales" },
 { label:"Marketing", value:"marketing" },
 { label:"Engineering", value:"engineering" },
 { label:"Support", value:"support" },
 { label:"Finance", value:"finance" },
 { label:"HR", value:"hr" },
 { label:"Operations", value:"operations" },
]

const ROLE_OPTIONS = [
 { label:"All Roles", value:"" },
 { label:"Executive", value:"executive" },
 { label:"Manager", value:"manager" },
 { label:"Sales Rep", value:"sales_rep" },
 { label:"Engineer", value:"engineer" },
 { label:"Analyst", value:"analyst" },
 { label:"Admin", value:"admin" },
]

function TrendIcon({ trend }: { trend: string | null | undefined }) {
 if (!trend) return null
 if (trend ==="up") return <TrendingUp className="h-3.5 w-3.5 text-success-500" />
 if (trend ==="down") return <TrendingDown className="h-3.5 w-3.5 text-danger-500" />
 return <Minus className="h-3.5 w-3.5 text-[var(--text-disabled)]" />
}

export default function EmployeesPage() {
 const router = useRouter()
 const searchParams = useSearchParams()
 const { t } = useTranslation()
 const { toast } = useToast()

 const [searchQuery, setSearchQuery] = useState(searchParams.get("q") ||"")
 const [departmentFilter, setDepartmentFilter] = useState(searchParams.get("department") ||"")
 const [roleFilter, setRoleFilter] = useState(searchParams.get("role") ||"")
 const [signalMin, setSignalMin] = useState(searchParams.get("signal_min") ||"")
 const [signalMax, setSignalMax] = useState(searchParams.get("signal_max") ||"")
 const [cursor, setCursor] = useState<string | null>(null)
 const [cursors, setCursors] = useState<string[]>([])
 const debouncedQuery = useDebounce(searchQuery, 400)

 const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
 const [selectAllAcross, setSelectAllAcross] = useState(false)

 const [bulkEditOpen, setBulkEditOpen] = useState(false)
 const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

 const [editDepartment, setEditDepartment] = useState("")
 const [editRole, setEditRole] = useState("")
 const [editStatus, setEditStatus] = useState("")

 const [expandedRow, setExpandedRow] = useState<string | null>(null)
 const [showAddModal, setShowAddModal] = useState(false)

 const [exportLoading, setExportLoading] = useState(false)

 const params: Record<string, unknown> = { page_size: 20 }
 if (debouncedQuery) params.q = debouncedQuery
 if (departmentFilter) params.department = departmentFilter
 if (roleFilter) params.role = roleFilter
 if (signalMin) params.signal_count_min = Number(signalMin)
 if (signalMax) params.signal_count_max = Number(signalMax)
 if (cursor) params.cursor = cursor

 const activeFilterCount = [departmentFilter, roleFilter, signalMin, signalMax].filter(Boolean).length

 const { data, isLoading, isError, error, refetch } = useEmployeeSearch(params)
 const bulkEdit = useBulkEditEmployees()
 const bulkDelete = useBulkDeleteEmployees()

 const items = data?.data || []
 const total = (data?.total ?? 0) as number
 const hasNext = data?.has_next ?? false
 const hasPrev = data?.has_previous ?? false

 const selectionCount = selectAllAcross && total ? total : selectedIds.size

 const handleSelect = useCallback((selected: EmployeeListItem[]) => {
 setSelectedIds(new Set(selected.map((e) => e.id)))
 }, [])

 const handleSelectAllAcross = useCallback(() => {
 setSelectAllAcross(true)
 if (data) setSelectedIds(new Set(data.data.map((e) => e.id)))
 }, [data])

 const handleClearSelection = useCallback(() => {
 setSelectedIds(new Set())
 setSelectAllAcross(false)
 }, [])

 const handleNextPage = useCallback(() => {
 if (hasNext && data && data.data.length > 0) {
 const lastItem = data.data[data.data.length - 1]
 setCursors((prev) => [...prev, cursor ||""])
 setCursor(lastItem.id)
 window.scrollTo(0, 0)
 }
 }, [hasNext, data, cursor])

 const handlePrevPage = useCallback(() => {
 if (cursors.length > 0) {
 const prev = cursors[cursors.length - 1]
 setCursors((prevC) => prevC.slice(0, -1))
 setCursor(prev || null)
 window.scrollTo(0, 0)
 }
 }, [cursors])

 const handleBulkEdit = useCallback(async () => {
 const ids = selectAllAcross && data ? [] : Array.from(selectedIds)
 if (!ids.length && !selectAllAcross) return
 try {
 const payload: Record<string, unknown> = {}
 if (editDepartment) payload.department = editDepartment
 if (editRole) payload.role = editRole
 if (editStatus) payload.status = editStatus
 if (selectAllAcross) payload.all = true
 else payload.ids = ids
 await bulkEdit.mutateAsync(payload as any)
 setBulkEditOpen(false)
 setEditDepartment("")
 setEditRole("")
 setEditStatus("")
 handleClearSelection()
 toast({ variant:"success", title: t("common.success"), description: `${selectionCount} ${t("employees.bulk_edit").toLowerCase()}d` })
 } catch {
 toast({ variant:"error", title: t("common.error"), description:"Bulk edit failed" })
 }
 }, [selectedIds, selectAllAcross, data, editDepartment, editRole, editStatus, bulkEdit, handleClearSelection, toast, selectionCount, t])

 const handleBulkDelete = useCallback(async () => {
 const ids = selectAllAcross && data ? data.data.map((e) => e.id) : Array.from(selectedIds)
 if (!ids.length) return
 try {
 await bulkDelete.mutateAsync(ids)
 setBulkDeleteOpen(false)
 handleClearSelection()
 toast({ variant:"success", title: t("common.success"), description: `${ids.length} employees deleted` })
 } catch {
 toast({ variant:"error", title: t("common.error"), description:"Bulk delete failed" })
 }
 }, [selectedIds, selectAllAcross, data, bulkDelete, handleClearSelection, toast])

 const handleBulkExport = useCallback(async () => {
 setExportLoading(true)
 try {
 const exportParams = new URLSearchParams()
 exportParams.set("format","csv")
 Object.entries(params).forEach(([k, v]) => {
 if (v !== undefined && v !=="" && v !== null) exportParams.set(k, String(v))
 })
 const response = await fetch(`/api/v1/employees/export?${exportParams.toString()}`, {
 headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}`,"X-Tenant-Id": localStorage.getItem("tenant_id") ||"default" },
 })
 if (!response.ok) throw new Error("Export failed")
 const blob = await response.blob()
 const url = URL.createObjectURL(blob)
 const a = document.createElement("a")
 a.href = url
 a.download = `employees-export-${new Date().toISOString().split("T")[0]}.csv`
 a.click()
 URL.revokeObjectURL(url)
 handleClearSelection()
 toast({ variant:"success", title:"Export complete", description:"Employees CSV has been downloaded." })
 } catch {
 toast({ variant:"error", title:"Export failed", description:"An error occurred while exporting." })
 } finally {
 setExportLoading(false)
 }
 }, [params, handleClearSelection, toast])

 const handleClearFilters = useCallback(() => {
 setDepartmentFilter("")
 setRoleFilter("")
 setSignalMin("")
 setSignalMax("")
 setSearchQuery("")
 setCursor(null)
 setCursors([])
 }, [])

 const columns: ColumnDef<EmployeeListItem>[] = [
 {
 accessorKey:"full_name",
 header: t("employees.name"),
 cell: ({ row }) => (
 <Link
 href={`/employees/${row.original.id}`}
                        className="flex items-center gap-2 font-medium text-[var(--muhide-orange)] hover:underline"
 >
 <User className="h-4 w-4 shrink-0 text-[var(--text-disabled)]" />
 <span className="truncate">{row.original.full_name_ar || row.original.full_name}</span>
 </Link>
 ),
 },
 {
 accessorKey:"role",
 header: t("employees.role"),
 cell: ({ getValue }) => {
 const role = getValue() as string
 return <span className="text-sm text-[var(--text-secondary)]">{role}</span>
 },
 },
 {
 accessorKey:"department",
 header: t("employees.department"),
 cell: ({ getValue }) => {
 const dept = getValue() as string | null
 return dept ? (
 <Badge variant="default" className="text-xs">{dept}</Badge>
 ) : (
 <span className="text-[var(--text-disabled)]">—</span>
 )
 },
 },
 {
 accessorKey:"email",
 header:"Email",
 cell: ({ getValue }) => {
 const email = getValue() as string
 return <span className="text-sm text-[var(--text-muted)]">{email}</span>
 },
 },
 {
 accessorKey:"signal_count",
 header: t("employees.signal_count"),
 cell: ({ row }) => {
 const count = row.original.signal_count
 return (
 <button
 onClick={(e) => { e.stopPropagation(); setExpandedRow(expandedRow === row.original.id ? null : row.original.id) }}
                        className="inline-flex items-center gap-1.5 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
 >
 <Signal className="h-3 w-3" />
 {count}
 </button>
 )
 },
 },
 {
 accessorKey:"score",
 header: t("employees.score"),
 cell: ({ row }) => (
 <div className="flex items-center gap-1.5">
 <ScoreBadge score={row.original.score} />
 <TrendIcon trend={row.original.score_trend} />
 </div>
 ),
 },
 {
 id:"actions",
 header:"",
 cell: ({ row }) => (
 <Link
 href={`/employees/${row.original.id}`}
                        className="inline-flex items-center gap-1 text-sm text-[var(--muhide-orange)] hover:underline"
 >
 {t("employees.details")}
 <ChevronLeft className="h-3 w-3" />
 </Link>
 ),
 },
 ]

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("employees.title")}</h1>
 <p className="mt-1 text-sm text-[var(--text-muted)]">{t("employees.subtitle")}</p>
 </div>
 <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowAddModal(true)}>{t("employees.add_employee")}</Button>
 </div>

 {/* Filters */}
 <div className="space-y-3">
 <div className="flex flex-wrap gap-3">
 <Input
 placeholder={t("employees.search_placeholder")}
 value={searchQuery}
 onChange={(e) => { setSearchQuery(e.target.value); setCursor(null); setCursors([]) }}
 leftIcon={<Search className="h-4 w-4" />}
 className="flex-1 min-w-[200px]"
 />
 <div className="w-40">
 <Select
 options={DEPARTMENT_OPTIONS}
 placeholder={t("employees.filter_department")}
 value={departmentFilter}
 onChange={(v) => { setDepartmentFilter(v); setCursor(null); setCursors([]) }}
 />
 </div>
 <div className="w-40">
 <Select
 options={ROLE_OPTIONS}
 placeholder={t("employees.filter_role")}
 value={roleFilter}
 onChange={(v) => { setRoleFilter(v); setCursor(null); setCursors([]) }}
 />
 </div>
 <div className="w-32">
 <Input
 type="number"
 placeholder={t("employees.filter_signals_min")}
 value={signalMin}
 onChange={(e) => { setSignalMin(e.target.value); setCursor(null); setCursors([]) }}
 />
 </div>
 <div className="w-32">
 <Input
 type="number"
 placeholder={t("employees.filter_signals_max")}
 value={signalMax}
 onChange={(e) => { setSignalMax(e.target.value); setCursor(null); setCursors([]) }}
 />
 </div>
 </div>

 {/* Active filter chips */}
 {activeFilterCount > 0 && (
 <div className="flex flex-wrap items-center gap-2">
 {departmentFilter && (
 <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
 {t("employees.filter_department")}: {departmentFilter}
 <button onClick={() => { setDepartmentFilter(""); setCursor(null); setCursors([]) }} className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)]"><X className="h-3 w-3" /></button>
 </span>
 )}
 {roleFilter && (
 <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
 {t("employees.filter_role")}: {roleFilter}
 <button onClick={() => { setRoleFilter(""); setCursor(null); setCursors([]) }} className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)]"><X className="h-3 w-3" /></button>
 </span>
 )}
 {signalMin && (
 <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
 Min signals: {signalMin}
 <button onClick={() => { setSignalMin(""); setCursor(null); setCursors([]) }} className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)]"><X className="h-3 w-3" /></button>
 </span>
 )}
 {signalMax && (
 <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
 Max signals: {signalMax}
 <button onClick={() => { setSignalMax(""); setCursor(null); setCursors([]) }} className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)]"><X className="h-3 w-3" /></button>
 </span>
 )}
 <button onClick={handleClearFilters} className="text-xs text-[var(--muhide-orange)] hover:underline">Clear all</button>
 </div>
 )}
 </div>

 {/* Bulk Selection Bar */}
 {selectionCount > 0 && (
 <div className="flex items-center gap-3 rounded-lg border border-[var(--muhide-orange)]/30 bg-[var(--muhide-orange)]/5 px-4 py-2.5">
 <Checkbox checked onChange={() => handleClearSelection()} />
            <span className="text-sm font-medium text-[var(--text-secondary)]">
 {selectAllAcross && data
 ? t("employees.selected_across", { count: selectionCount, total })
 : t("employees.selected_count", { count: selectionCount })}
 </span>
 {!selectAllAcross && data && total > data.data.length && (
 <button onClick={handleSelectAllAcross} className="text-xs text-[var(--muhide-orange)] hover:underline">
 {t("employees.select_all", { total })}
 </button>
 )}
 <div className="flex-1" />
 <Button size="sm" variant="outline" leftIcon={<Edit3 className="h-4 w-4" />} onClick={() => setBulkEditOpen(true)}>
 {t("employees.bulk_edit")}
 </Button>
 <Button size="sm" variant="outline" leftIcon={<Download className="h-4 w-4" />} onClick={handleBulkExport} disabled={exportLoading}>
 {exportLoading ?"Exporting..." : t("employees.bulk_export")}
 </Button>
 <Button size="sm" variant="outline" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setBulkDeleteOpen(true)} className="text-danger-600 border-danger-300 hover:bg-danger-50 dark:border-danger-700 dark:hover:bg-danger-900/20">
 {t("employees.bulk_delete")}
 </Button>
 </div>
 )}

 {/* Table */}
 <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {isLoading ? (
 <div className="space-y-3 p-4">
 {Array.from({ length: 5 }).map((_, i) => (
 <div key={i} className="flex items-center gap-4">
 <Skeleton className="h-8 w-8 rounded-full" />
 <Skeleton className="h-4 flex-1" />
 <Skeleton className="h-4 w-24" />
 <Skeleton className="h-4 w-20" />
 </div>
 ))}
 </div>
 ) : isError ? (
 <div className="px-4 py-12">
 <ErrorFallback
 title={t("employees.load_error")}
 message={(error as Error)?.message || t("employees.check_backend")}
 onRetry={() => refetch()}
 showDetails={process.env.NODE_ENV ==="development"}
 errorDetails={String(error)}
 />
 </div>
 ) : items.length === 0 ? (
 <div className="px-4 py-12">
 <EmptyState
 icon={<User className="h-10 w-10" />}
 title={searchQuery || activeFilterCount > 0 ? t("employees.no_search_results") : t("employees.empty")}
 description={searchQuery || activeFilterCount > 0 ? t("activities.try_different_search") : t("employees.empty_hint")}
 />
 </div>
 ) : (
 <DataTable<EmployeeListItem>
 columns={columns}
 data={items}
 selectable
 onSelect={handleSelect}
 onRowClick={(row) => router.push(`/employees/${row.id}`)}
 />
 )}
 </div>

 {/* Expanded Row — Signals Dashboard (F-2) + Score Detail (F-3) */}
 {expandedRow && data && (
 <EmployeeDetailPanel employeeId={expandedRow} employee={items.find((e) => e.id === expandedRow)} onClose={() => setExpandedRow(null)} />
 )}

 {/* Keyset Pagination (F-1) */}
 {total > 0 && (
 <div className="flex items-center justify-between">
 <p className="text-sm text-[var(--text-muted)]">
 {t("employees.pagination", { total, page: cursors.length + 1, totalPages:"—" })}
 </p>
 <div className="flex items-center gap-2">
 <Button variant="outline" size="sm" onClick={handlePrevPage} disabled={!hasPrev && cursors.length === 0} leftIcon={<ChevronRight className="h-4 w-4" />} />
 <span className="text-sm text-[var(--text-muted)]">{cursors.length + 1}</span>
 <Button variant="outline" size="sm" onClick={handleNextPage} disabled={!hasNext} leftIcon={<ChevronLeft className="h-4 w-4" />} />
 </div>
 </div>
 )}

 {/* Bulk Edit Modal (F-4) */}
 <Modal open={bulkEditOpen} onOpenChange={setBulkEditOpen}>
 <ModalContent>
 <ModalHeader>{t("employees.bulk_edit_title", { count: selectionCount })}</ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("employees.department")}</label>
 <Select
 options={DEPARTMENT_OPTIONS.slice(1)}
 placeholder={t("employees.filter_department")}
 value={editDepartment}
 onChange={setEditDepartment}
 />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("employees.role")}</label>
 <Select
 options={ROLE_OPTIONS.slice(1)}
 placeholder={t("employees.filter_role")}
 value={editRole}
 onChange={setEditRole}
 />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.status")}</label>
 <Select
 options={[{ label:"Active", value:"active" }, { label:"Inactive", value:"inactive" }]}
 placeholder="Select status"
 value={editStatus}
 onChange={setEditStatus}
 />
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setBulkEditOpen(false)}>{t("common.cancel")}</Button>
 <Button onClick={handleBulkEdit} disabled={bulkEdit.isPending} leftIcon={bulkEdit.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {bulkEdit.isPending ? t("common.saving") : t("common.save")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 {/* Bulk Delete Confirmation (F-4) */}
 <Modal open={bulkDeleteOpen} onOpenChange={setBulkDeleteOpen}>
 <ModalContent>
 <ModalHeader>{t("employees.bulk_delete_title")}</ModalHeader>
 <ModalBody>
 <div className="space-y-3">
 <p className="text-[var(--text-secondary)]" dangerouslySetInnerHTML={{ __html: t("employees.bulk_delete_message", { count: selectionCount }) }} />
 <p className="text-sm text-danger-600">{t("employees.bulk_delete_warning")}</p>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setBulkDeleteOpen(false)}>{t("common.cancel")}</Button>
 <Button
 onClick={handleBulkDelete}
 disabled={bulkDelete.isPending}
 className="bg-danger-600 text-white hover:bg-danger-700 focus:ring-danger-500"
 leftIcon={bulkDelete.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
 >
 {bulkDelete.isPending ? t("common.deleting") : t("employees.bulk_delete_confirm", { count: selectionCount })}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 {/* Add Employee Modal */}
 <Modal open={showAddModal} onOpenChange={setShowAddModal}>
 <ModalContent>
 <ModalHeader>{t("employees.add_employee")}</ModalHeader>
 <ModalBody>
 <p className="text-sm text-[var(--text-secondary)]">{t("employees.add_employee_description")}</p>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setShowAddModal(false)}>{t("common.cancel")}</Button>
 <Button onClick={() => setShowAddModal(false)}>{t("common.save")}</Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>
 )
}

function EmployeeDetailPanel({ employeeId, employee, onClose }: { employeeId: string; employee?: EmployeeListItem; onClose: () => void }) {
 const { t } = useTranslation()
 const { data: signals, isLoading: signalsLoading } = useEmployeeSignals(employeeId)
 const [activeTab, setActiveTab] = useState<"signals" |"score">("signals")

 return (
 <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)] p-4/50">
 <div className="flex items-center justify-between mb-4">
 <h3 className="text-lg font-bold text-[var(--text-primary)]">
 {employee?.full_name_ar || employee?.full_name || employeeId}
 </h3>
 <Button variant="outline" size="sm" onClick={onClose} leftIcon={<X className="h-3 w-3" />}>Close</Button>
 </div>

 {/* Tab switcher */}
 <div className="flex items-center gap-2 mb-4">
 <button
 onClick={() => setActiveTab("signals")}
 className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="signals" ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]" :"text-[var(--text-muted)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
 }`}
 >
 <Activity className="h-4 w-4" />
 {t("employees.signals_title")}
 </button>
 <button
 onClick={() => setActiveTab("score")}
 className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
 activeTab ==="score" ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]" :"text-[var(--text-muted)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
 }`}
 >
 <Brain className="h-4 w-4" />
 {t("employees.score_title")}
 </button>
 </div>

 {activeTab ==="signals" && (
 signalsLoading ? (
 <div className="grid grid-cols-3 gap-4">
 {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)}
 </div>
 ) : signals ? (
 <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
 {/* Signal type breakdown (F-2) */}
 <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
 <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
 <PieChart className="h-3.5 w-3.5" />
 {t("employees.signals_by_type")}
 </h4>
 <div className="space-y-1.5">
 {signals.by_type.map((s) => (
 <div key={s.type} className="flex items-center justify-between text-xs">
 <span className="text-[var(--text-secondary)]">{s.label}</span>
 <span className="font-medium text-[var(--text-primary)]">{s.count}</span>
 </div>
 ))}
 {signals.by_type.length === 0 && <p className="text-xs text-[var(--text-disabled)]">No signals</p>}
 </div>
 </div>

 {/* Source breakdown (F-2) */}
 <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
 <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
 <BarChart3 className="h-3.5 w-3.5" />
 {t("employees.signals_by_source")}
 </h4>
 <div className="space-y-1.5">
 {signals.by_source.map((s) => (
 <div key={s.source} className="flex items-center justify-between text-xs">
 <span className="text-[var(--text-secondary)]">{s.label}</span>
 <span className="font-medium text-[var(--text-primary)]">{s.count}</span>
 </div>
 ))}
 {signals.by_source.length === 0 && <p className="text-xs text-[var(--text-disabled)]">No sources</p>}
 </div>
 </div>

 {/* Trend (F-2) */}
 <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
 <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
 <TrendingUp className="h-3.5 w-3.5" />
 {t("employees.signals_trend")}
 </h4>
 <div className="space-y-1.5">
 {signals.trend.map((p) => (
 <div key={p.date} className="flex items-center justify-between text-xs">
 <span className="text-[var(--text-muted)]">{p.date}</span>
 <div className="flex items-center gap-1">
 <div className="h-2 rounded-full bg-[var(--muhide-orange)]" style={{ width: `${Math.min(100, p.count * 10)}px` }} />
 <span className="font-medium text-[var(--text-secondary)]">{p.count}</span>
 </div>
 </div>
 ))}
 {signals.trend.length === 0 && <p className="text-xs text-[var(--text-disabled)]">No trend data</p>}
 </div>
 <p className="mt-2 text-center text-[10px] text-[var(--text-disabled)]">{t("employees.signals_total", { count: signals.total })}</p>
 </div>
 </div>
 ) : (
 <EmptyState icon={<Activity className="h-8 w-8" />} title="No signal data" />
 )
 )}

 {activeTab ==="score" && (
 <EmployeeScorePanel employeeId={employeeId} />
 )}
 </div>
 )
}

function EmployeeScorePanel({ employeeId }: { employeeId: string }) {
 const { t } = useTranslation()
 const { data: scoreData, isLoading } = useEmployeeScore(employeeId)

 if (isLoading) {
 return <Skeleton className="h-32 rounded-lg" />
 }

 if (!scoreData) {
 return <EmptyState icon={<Brain className="h-8 w-8" />} title="No score data" />
 }

 const gaugeColor = scoreData.score >= 70 ?"stroke-success-500" :
 scoreData.score >= 40 ?"stroke-warning-500" :"stroke-danger-500"

 const trendIcon = scoreData.trend ==="up" ? <TrendingUp className="h-4 w-4 text-success-500" /> :
 scoreData.trend ==="down" ? <TrendingDown className="h-4 w-4 text-danger-500" /> :
 <Minus className="h-4 w-4 text-[var(--text-disabled)]" />

 return (
 <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
 {/* Score Gauge (F-3) */}
 <div className="flex flex-col items-center justify-center rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
 <div className="relative mb-2">
 <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
 <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-[var(--text-primary)]" />
 <circle
 cx="50" cy="50" r="42" fill="none"
 strokeWidth="8" strokeLinecap="round"
 className={gaugeColor}
 strokeDasharray={`${(scoreData.score / 100) * 263.9} 263.9`}
 />
 </svg>
 <div className="absolute inset-0 flex items-center justify-center">
 <span className="text-2xl font-bold text-[var(--text-primary)]">{scoreData.score}</span>
 </div>
 </div>
 <div className="flex items-center gap-1 text-sm">
 <span className="text-[var(--text-muted)]">{t("employees.score_trend")}:</span>
 {trendIcon}
 <span className="text-xs text-[var(--text-disabled)] capitalize">{scoreData.trend}</span>
 </div>
 </div>

 {/* Factors Breakdown (F-3) */}
 <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 md:col-span-2">
 <h4 className="mb-3 flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
 <BarChart3 className="h-3.5 w-3.5" />
 {t("employees.score_factors")}
 </h4>
 <div className="space-y-2">
 {scoreData.factors.map((f) => (
 <div key={f.name}>
 <div className="flex items-center justify-between text-xs">
 <span className="text-[var(--text-secondary)]">{f.label}</span>
 <span className="font-medium text-[var(--text-primary)]">+{f.contribution}</span>
 </div>
 <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
 <div
 className="h-full rounded-full bg-[var(--muhide-orange)]"
 style={{ width: `${Math.min(100, f.contribution * 5)}%` }}
 />
 </div>
 </div>
 ))}
 {scoreData.factors.length === 0 && <p className="text-xs text-[var(--text-disabled)]">No factors available</p>}
 </div>
 </div>

 {/* Confidence (F-3) */}
 <div className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2">
 <span className="text-xs text-[var(--text-muted)]">{t("employees.score_confidence")}:</span>
 <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
 <div
 className="h-full rounded-full bg-info-500"
 style={{ width: `${scoreData.confidence}%` }}
 />
 </div>
 <span className="text-xs font-medium text-[var(--text-secondary)]">{Math.round(scoreData.confidence)}%</span>
 </div>
 </div>
 )
}

// Lazy imports for the expanded detail panel

