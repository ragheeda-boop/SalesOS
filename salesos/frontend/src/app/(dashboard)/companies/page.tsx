"use client"

import { useState, useCallback, useMemo } from"react"
import Link from"next/link"
import { useRouter, useSearchParams } from"next/navigation"
import { useCompanySearch } from"@/lib/hooks/companyQueries"
import { useCreateCompany, useUpdateCompany, useDeleteCompany } from"@/lib/hooks/mutationHooks"
import { useDebounce } from"@salesos/hooks"
import { DataTable, Checkbox, Input, Badge, Button, Spinner, Select, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, Combobox, DatePicker, useToast, Pagination } from"@salesos/ui"
import { Search, Plus, Building2, ArrowLeft, ChevronLeft, ChevronRight, Loader2, MapPin, Hash, Download, Edit3, Trash2, X } from"lucide-react"
import { ErrorFallback } from"@/components/foundation/error-boundary"
import { useTranslation } from"@/lib/i18n"
import type { ColumnDef } from"@tanstack/react-table"
import type { Company } from"@/lib/api"

const STATUS_OPTIONS = [
 { label:"All", value:"" },
 { label:"Active", value:"active" },
 { label:"Inactive", value:"inactive" },
 { label:"Suspended", value:"suspended" },
 { label:"Expired", value:"expired" },
]

const STATUS_VARIANT: Record<string,"success" |"warning" |"danger" |"default"> = {
 active:"success",
 inactive:"default",
 suspended:"warning",
 expired:"danger",
}

const INDUSTRY_OPTIONS = [
 { label:"Technology", value:"technology" },
 { label:"Healthcare", value:"healthcare" },
 { label:"Finance", value:"finance" },
 { label:"Real Estate", value:"real_estate" },
 { label:"Manufacturing", value:"manufacturing" },
 { label:"Retail", value:"retail" },
 { label:"Energy", value:"energy" },
 { label:"Education", value:"education" },
 { label:"Construction", value:"construction" },
 { label:"Transportation", value:"transportation" },
]

const REGION_OPTIONS = [
 { label:"All Regions", value:"" },
 { label:"Riyadh", value:"riyadh" },
 { label:"Makkah", value:"makkah" },
 { label:"Eastern Province", value:"eastern" },
 { label:"Madinah", value:"madinah" },
 { label:"Qassim", value:"qassim" },
 { label:"Asir", value:"asir" },
 { label:"Tabuk", value:"tabuk" },
 { label:"Hail", value:"hail" },
 { label:"Northern Borders", value:"northern_borders" },
 { label:"Jazan", value:"jazan" },
 { label:"Najran", value:"najran" },
 { label:"Al Bahah", value:"al_bahah" },
 { label:"Al Jawf", value:"al_jawf" },
]

export default function CompaniesPage() {
 const router = useRouter()
 const searchParams = useSearchParams()
 const { t } = useTranslation()
 const { toast } = useToast()

 const [searchQuery, setSearchQuery] = useState(searchParams.get("q") ||"")
 const [statusFilter, setStatusFilter] = useState(searchParams.get("status") ||"")
 const [page, setPage] = useState(Number(searchParams.get("page")) || 1)
 const [modalOpen, setModalOpen] = useState(false)
 const [formData, setFormData] = useState({ name_ar:"", cr_number:"", name_en:"", city:"", region:"" })
 const debouncedQuery = useDebounce(searchQuery, 400)

 const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
 const [selectAllAcross, setSelectAllAcross] = useState(false)

 const [bulkEditOpen, setBulkEditOpen] = useState(false)
 const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

 const [bulkEditForm, setBulkEditForm] = useState({ industry:"", size:"", status:"", tags:"" })

 const [editIndustry, setEditIndustry] = useState("")
 const [editSize, setEditSize] = useState("")
 const [editStatus, setEditStatus] = useState("")
 const [editTags, setEditTags] = useState("")

 const [filterIndustry, setFilterIndustry] = useState(searchParams.get("industry") ||"")
 const [filterSizeMin, setFilterSizeMin] = useState(searchParams.get("size_min") ||"")
 const [filterSizeMax, setFilterSizeMax] = useState(searchParams.get("size_max") ||"")
 const [filterRegion, setFilterRegion] = useState(searchParams.get("region") ||"")
 const [filterDateFrom, setFilterDateFrom] = useState<Date | null>(searchParams.get("date_from") ? new Date(searchParams.get("date_from")!) : null)
 const [filterDateTo, setFilterDateTo] = useState<Date | null>(searchParams.get("date_to") ? new Date(searchParams.get("date_to")!) : null)
 const [filterStatusChips, setFilterStatusChips] = useState<string[]>(searchParams.get("status") ? searchParams.get("status")!.split(",").filter(Boolean) : [])

 const [exportLoading, setExportLoading] = useState(false)

 const params: Record<string, unknown> = { page, page_size: 20 }
 if (debouncedQuery) params.q = debouncedQuery
 if (statusFilter) params.status = statusFilter
 if (filterIndustry) params.industry = filterIndustry
 if (filterSizeMin) params.size_min = Number(filterSizeMin)
 if (filterSizeMax) params.size_max = Number(filterSizeMax)
 if (filterRegion) params.region = filterRegion
 if (filterDateFrom) params.date_from = filterDateFrom.toISOString()
 if (filterDateTo) params.date_to = filterDateTo.toISOString()
 if (filterStatusChips.length) params.status = filterStatusChips.join(",")

 const { data, isLoading, isError, error, refetch } = useCompanySearch(params)
 const createCompany = useCreateCompany()
 const updateCompany = useUpdateCompany()
 const deleteCompany = useDeleteCompany()

 const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1

 const activeFilterCount = [filterIndustry, filterRegion, filterSizeMin, filterSizeMax, filterDateFrom, filterDateTo, ...filterStatusChips].filter(Boolean).length

 const visibleData = data?.items || []

 const handleSelect = useCallback((selected: Company[]) => {
 setSelectedIds(new Set(selected.map((c) => c.id)))
 }, [])

 const handleSelectAllAcross = useCallback(() => {
 setSelectAllAcross(true)
 if (data) {
 setSelectedIds(new Set(data.items.map((c) => c.id)))
 }
 }, [data])

 const handleClearSelection = useCallback(() => {
 setSelectedIds(new Set())
 setSelectAllAcross(false)
 }, [])

 const selectionCount = selectAllAcross && data ? data.total : selectedIds.size

 const handleCreate = useCallback(async () => {
 if (!formData.name_ar || !formData.cr_number) return
 try {
 await createCompany.mutateAsync({
 name_ar: formData.name_ar,
 cr_number: formData.cr_number,
 name_en: formData.name_en || undefined,
 city: formData.city || undefined,
 region: formData.region || undefined,
 })
 setModalOpen(false)
 setFormData({ name_ar:"", cr_number:"", name_en:"", city:"", region:"" })
 setPage(1)
 toast({ variant:"success", title:"Company created", description:"The company has been added successfully." })
 } catch {
 toast({ variant:"error", title:"Failed to create", description:"An error occurred while creating the company." })
 }
 }, [formData, createCompany, toast])

 const handleBulkEdit = useCallback(async () => {
 const ids = selectAllAcross && data ? data.items.map((c) => c.id) : Array.from(selectedIds)
 if (!ids.length) return
 try {
 const payload: Record<string, unknown> = {}
 if (editIndustry) payload.industry = editIndustry
 if (editSize) payload.size = Number(editSize)
 if (editStatus) payload.status = editStatus
 if (editTags) payload.tags = editTags.split(",").map((t: string) => t.trim())
 await Promise.all(ids.map((id) => updateCompany.mutateAsync({ id, ...payload })))
 setBulkEditOpen(false)
 setEditIndustry("")
 setEditSize("")
 setEditStatus("")
 setEditTags("")
 handleClearSelection()
 toast({ variant:"success", title:"Companies updated", description: `${ids.length} companies have been updated.` })
 } catch {
 toast({ variant:"error", title:"Bulk edit failed", description:"An error occurred while updating companies." })
 }
 }, [selectedIds, selectAllAcross, data, editIndustry, editSize, editStatus, editTags, updateCompany, handleClearSelection, toast])

 const handleBulkDelete = useCallback(async () => {
 const ids = selectAllAcross && data ? data.items.map((c) => c.id) : Array.from(selectedIds)
 if (!ids.length) return
 try {
 await Promise.all(ids.map((id) => deleteCompany.mutateAsync({ id })))
 setBulkDeleteOpen(false)
 handleClearSelection()
 toast({ variant:"success", title:"Companies deleted", description: `${ids.length} companies have been deleted.` })
 } catch {
 toast({ variant:"error", title:"Bulk delete failed", description:"An error occurred while deleting companies." })
 }
 }, [selectedIds, selectAllAcross, data, deleteCompany, handleClearSelection, toast])

 const handleBulkExport = useCallback(async () => {
 setExportLoading(true)
 try {
 const ids = selectAllAcross && data ? [] : Array.from(selectedIds)
 const exportParams = new URLSearchParams()
 exportParams.set("format","csv")
 if (ids.length) ids.forEach((id) => exportParams.append("ids", id))
 Object.entries(params).forEach(([k, v]) => {
 if (v !== undefined && v !=="" && v !== null) exportParams.set(k, String(v))
 })
 const response = await fetch(`/api/v1/companies/export?${exportParams.toString()}`, {
 headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}`,"X-Tenant-Id": localStorage.getItem("tenant_id") ||"default" },
 })
 if (!response.ok) throw new Error("Export failed")
 const blob = await response.blob()
 const url = URL.createObjectURL(blob)
 const a = document.createElement("a")
 a.href = url
 a.download = `companies-export-${new Date().toISOString().split("T")[0]}.csv`
 a.click()
 URL.revokeObjectURL(url)
 handleClearSelection()
 toast({ variant:"success", title:"Export complete", description:"Companies CSV has been downloaded." })
 } catch {
 toast({ variant:"error", title:"Export failed", description:"An error occurred while exporting companies." })
 } finally {
 setExportLoading(false)
 }
 }, [selectedIds, selectAllAcross, data, params, handleClearSelection, toast])

 const handleFilterStatusToggle = useCallback((status: string) => {
 setFilterStatusChips((prev) => prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status])
 setPage(1)
 }, [])

 const handleClearFilters = useCallback(() => {
 setFilterIndustry("")
 setFilterSizeMin("")
 setFilterSizeMax("")
 setFilterRegion("")
 setFilterDateFrom(null)
 setFilterDateTo(null)
 setFilterStatusChips([])
 setSearchQuery("")
 setPage(1)
 }, [])

 const filterChips = useMemo(() => {
 const chips: { label: string; onRemove: () => void }[] = []
 if (filterIndustry) chips.push({ label: `Industry: ${filterIndustry}`, onRemove: () => { setFilterIndustry(""); setPage(1) } })
 if (filterSizeMin) chips.push({ label: `Min size: ${filterSizeMin}`, onRemove: () => { setFilterSizeMin(""); setPage(1) } })
 if (filterSizeMax) chips.push({ label: `Max size: ${filterSizeMax}`, onRemove: () => { setFilterSizeMax(""); setPage(1) } })
 if (filterRegion) chips.push({ label: `Region: ${filterRegion}`, onRemove: () => { setFilterRegion(""); setPage(1) } })
 if (filterDateFrom) chips.push({ label: `From: ${filterDateFrom.toLocaleDateString()}`, onRemove: () => { setFilterDateFrom(null); setPage(1) } })
 if (filterDateTo) chips.push({ label: `To: ${filterDateTo.toLocaleDateString()}`, onRemove: () => { setFilterDateTo(null); setPage(1) } })
 filterStatusChips.forEach((s) => chips.push({ label: `Status: ${s}`, onRemove: () => handleFilterStatusToggle(s) }))
 return chips
 }, [filterIndustry, filterSizeMin, filterSizeMax, filterRegion, filterDateFrom, filterDateTo, filterStatusChips, handleFilterStatusToggle])

 const columns: ColumnDef<Company>[] = [
 {
 accessorKey:"name_ar",
 header: t("companies.name"),
 cell: ({ row }) => (
 <Link
 href={`/companies/${row.original.id}`}
 className="flex items-center gap-2 font-medium text-[var(--muhide-orange)] hover:underline"
 >
 <Building2 className="h-4 w-4 shrink-0" />
 <span className="truncate">{row.original.name_ar || row.original.name_en}</span>
 </Link>
 ),
 },
 {
 accessorKey:"cr_number",
 header: t("companies.cr_number"),
 cell: ({ getValue }) => (
 <span className="inline-flex items-center gap-1 text-sm text-[var(--text-secondary)]">
 <Hash className="h-3 w-3 shrink-0 text-[var(--text-disabled)]" />
 {getValue() as string}
 </span>
 ),
 },
 {
 accessorKey:"status",
 header: t("labels.status"),
 cell: ({ getValue }) => {
 const status = getValue() as string
 return <Badge variant={STATUS_VARIANT[status] ||"default"}>{status}</Badge>
 },
 },
 {
 accessorKey:"city",
 header: t("labels.city"),
 cell: ({ getValue }) => {
 const city = getValue() as string | null
 return city ? (
 <span className="inline-flex items-center gap-1 text-sm text-[var(--text-secondary)]">
 <MapPin className="h-3 w-3 shrink-0 text-[var(--text-disabled)]" />
 {city}
 </span>
 ) : (
 <span className="text-[var(--text-disabled)]">-</span>
 )
 },
 },
 {
 id:"actions",
 header:"",
 cell: ({ row }) => (
 <Link
 href={`/companies/${row.original.id}`}
 className="inline-flex items-center gap-1 text-sm text-[var(--muhide-orange)] hover:underline"
 >
 {t("companies.details")}
 <ArrowLeft className="h-3 w-3" />
 </Link>
 ),
 },
 ]

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("nav.companies")}</h1>
 <p className="mt-1 text-sm text-[var(--text-muted)]">
 {t("companies.subtitle")}
 </p>
 </div>
 <Modal open={modalOpen} onOpenChange={setModalOpen}>
 <ModalTrigger>
 <Button leftIcon={<Plus className="h-4 w-4" />}>{t("companies.add_company")}</Button>
 </ModalTrigger>
 <ModalContent>
 <ModalHeader>{t("companies.add_new")}</ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("companies.name_ar")} *</label>
 <Input value={formData.name_ar} onChange={(e) => setFormData({ ...formData, name_ar: e.target.value })} placeholder="Al Amal Trading Co." />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("companies.cr_number_required")}</label>
 <Input value={formData.cr_number} onChange={(e) => setFormData({ ...formData, cr_number: e.target.value })} placeholder="1234567890" />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("companies.name_en")}</label>
 <Input value={formData.name_en} onChange={(e) => setFormData({ ...formData, name_en: e.target.value })} placeholder="Al Amal Trading Co." />
 </div>
 <div className="grid grid-cols-2 gap-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.city")}</label>
 <Input value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} placeholder="Riyadh" />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.region")}</label>
 <Input value={formData.region} onChange={(e) => setFormData({ ...formData, region: e.target.value })} placeholder="Riyadh Region" />
 </div>
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setModalOpen(false)}>{t("common.cancel")}</Button>
 <Button onClick={handleCreate} disabled={!formData.name_ar || !formData.cr_number || createCompany.isPending} leftIcon={createCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {createCompany.isPending ? t("common.saving") : t("common.save")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>

 {/* Advanced Filters (F-3) */}
 <div className="space-y-3">
 <div className="flex flex-wrap gap-3">
 <Input
 placeholder={t("companies.search_placeholder")}
 value={searchQuery}
 onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
 leftIcon={<Search className="h-4 w-4" />}
 className="flex-1 min-w-[200px]"
 />
 <div className="w-44">
 <Combobox
 options={INDUSTRY_OPTIONS}
 placeholder="Industry"
 value={filterIndustry}
 onChange={(v) => { setFilterIndustry(v); setPage(1) }}
 />
 </div>
 <div className="w-44">
 <Select
 options={REGION_OPTIONS}
 placeholder="Region"
 value={filterRegion}
 onChange={(v) => { setFilterRegion(v); setPage(1) }}
 />
 </div>
 <div className="w-32">
 <Input
 type="number"
 placeholder="Min size"
 value={filterSizeMin}
 onChange={(e) => { setFilterSizeMin(e.target.value); setPage(1) }}
 />
 </div>
 <div className="w-32">
 <Input
 type="number"
 placeholder="Max size"
 value={filterSizeMax}
 onChange={(e) => { setFilterSizeMax(e.target.value); setPage(1) }}
 />
 </div>
 <div className="w-48">
 <DatePicker
 mode="single"
 placeholder="From date"
 value={filterDateFrom}
 onChange={(v) => { setFilterDateFrom(v as Date | null); setPage(1) }}
 />
 </div>
 <div className="w-48">
 <DatePicker
 mode="single"
 placeholder="To date"
 value={filterDateTo}
 onChange={(v) => { setFilterDateTo(v as Date | null); setPage(1) }}
 />
 </div>
 </div>

 {/* Status chips */}
 <div className="flex flex-wrap items-center gap-2">
 <span className="text-sm text-[var(--text-muted)]">Status:</span>
 {["active","inactive","suspended","expired"].map((s) => (
 <button
 key={s}
 onClick={() => handleFilterStatusToggle(s)}
 className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
 filterStatusChips.includes(s)
 ?"bg-[var(--muhide-orange)] text-white"
 :"bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-neutral-700"
 }`}
 >
 {s}
 {filterStatusChips.includes(s) && <X className="h-3 w-3" />}
 </button>
 ))}
 </div>

 {/* Filter chips */}
 {filterChips.length > 0 && (
 <div className="flex flex-wrap items-center gap-2">
 {filterChips.map((chip, i) => (
 <span key={i} className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
 {chip.label}
 <button onClick={chip.onRemove} className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]" aria-label={t("companies.remove_filter", { label: chip.label })}>
 <X className="h-3 w-3" />
 </button>
 </span>
 ))}
 <button onClick={handleClearFilters} className="text-xs text-[var(--muhide-orange)] hover:underline">
 Clear all
 </button>
 </div>
 )}
 </div>

 {/* Bulk Selection Bar (F-1) */}
 {selectionCount > 0 && (
 <div className="flex items-center gap-3 rounded-lg border border-[var(--muhide-orange)]/30 bg-[var(--muhide-orange)]/5 px-4 py-2.5">
 <Checkbox checked onChange={() => handleClearSelection()} />
 <span className="text-sm font-medium text-[var(--text-secondary)]">
 {selectionCount} selected{selectAllAcross && data ? ` across all ${data.total} companies` :""}
 </span>
 {!selectAllAcross && data && data.total > data.items.length && (
 <button onClick={handleSelectAllAcross} className="text-xs text-[var(--muhide-orange)] hover:underline">
 Select all {data.total} companies across all pages
 </button>
 )}
 <div className="flex-1" />
 <Button size="sm" variant="outline" leftIcon={<Edit3 className="h-4 w-4" />} onClick={() => setBulkEditOpen(true)}>
 Edit
 </Button>
 <Button size="sm" variant="outline" leftIcon={<Download className="h-4 w-4" />} onClick={handleBulkExport} disabled={exportLoading}>
 {exportLoading ?"Exporting..." :"Export"}
 </Button>
 <Button size="sm" variant="outline" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setBulkDeleteOpen(true)} className="text-danger-600 border-danger-300 hover:bg-danger-50 dark:border-danger-700 dark:hover:bg-danger-900/20">
 Delete
 </Button>
 </div>
 )}

 {/* Table */}
 <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {isError ? (
 <div className="px-4 py-12">
 <ErrorFallback
 title={t("companies.load_error")}
 message={(error as Error)?.message || t("companies.check_backend")}
 onRetry={() => refetch()}
 showDetails={process.env.NODE_ENV ==="development"}
 errorDetails={String(error)}
 />
 </div>
 ) : (
 <DataTable<Company>
 columns={columns}
 data={visibleData}
 loading={isLoading}
 selectable
 onSelect={handleSelect}
 onRowClick={(row) => router.push(`/companies/${row.id}`)}
 emptyState={{
 icon: <Building2 className="h-10 w-10" />,
 title: searchQuery || activeFilterCount > 0 ? t("companies.no_search_results") : t("companies.empty"),
 description: searchQuery || activeFilterCount > 0 ? t("activities.try_different_search") : t("companies.empty_hint"),
 ...(!searchQuery && activeFilterCount === 0 ? { action: { label: t("companies.add_company"), onClick: () => setModalOpen(true) } } : {}),
 }}
 />
 )}
 </div>

 {/* Pagination */}
 {data && data.total > 0 && (
 <div className="flex items-center justify-between">
 <p className="text-sm text-[var(--text-muted)]">
 {t("companies.pagination", { total: data.total, page: page, totalPages: totalPages })}
 </p>
 <div className="flex items-center gap-2">
 <Button
 variant="outline"
 size="sm"
 onClick={() => setPage((p) => Math.max(1, p - 1))}
 disabled={page <= 1}
 leftIcon={<ChevronRight className="h-4 w-4" />}
 />
 {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
 const start = Math.max(1, Math.min(page - 2, totalPages - 4))
 const p = start + i
 if (p > totalPages) return null
 return (
 <Button
 key={p}
 variant={p === page ?"primary" :"outline"}
 size="sm"
 onClick={() => setPage(p)}
 >
 {p}
 </Button>
 )
 })}
 <Button
 variant="outline"
 size="sm"
 onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
 disabled={page >= totalPages}
 leftIcon={<ChevronLeft className="h-4 w-4" />}
 />
 </div>
 </div>
 )}

 {/* Bulk Edit Modal (F-2) */}
 <Modal open={bulkEditOpen} onOpenChange={setBulkEditOpen}>
 <ModalContent>
 <ModalHeader>Edit {selectionCount} Companies</ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">Industry</label>
 <Select
 options={INDUSTRY_OPTIONS.slice(1)}
 placeholder="Select industry"
 value={editIndustry}
 onChange={setEditIndustry}
 />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">Size (employees)</label>
 <Input type="number" placeholder="e.g. 50" value={editSize} onChange={(e) => setEditSize(e.target.value)} />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">Status</label>
 <Select
 options={STATUS_OPTIONS.slice(1)}
 placeholder="Select status"
 value={editStatus}
 onChange={setEditStatus}
 />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">Tags (comma separated)</label>
 <Input placeholder="e.g. vip, enterprise, saudi" value={editTags} onChange={(e) => setEditTags(e.target.value)} />
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setBulkEditOpen(false)}>Cancel</Button>
 <Button onClick={handleBulkEdit} disabled={updateCompany.isPending} leftIcon={updateCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {updateCompany.isPending ?"Saving..." :"Save Changes"}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 {/* Bulk Delete Confirmation (F-2) */}
 <Modal open={bulkDeleteOpen} onOpenChange={setBulkDeleteOpen}>
 <ModalContent>
 <ModalHeader>Confirm Deletion</ModalHeader>
 <ModalBody>
 <div className="space-y-3">
 <p className="text-[var(--text-secondary)]">
 Delete <strong>{selectionCount}</strong> companies?
 </p>
 <p className="text-sm text-danger-600">This action cannot be undone. All associated data will be permanently removed.</p>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setBulkDeleteOpen(false)}>Cancel</Button>
 <Button
 onClick={handleBulkDelete}
 disabled={deleteCompany.isPending}
 className="bg-danger-600 text-white hover:bg-danger-700 focus:ring-danger-500"
 leftIcon={deleteCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
 >
 {deleteCompany.isPending ?"Deleting..." : `Delete ${selectionCount} Companies`}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>
 )
}
