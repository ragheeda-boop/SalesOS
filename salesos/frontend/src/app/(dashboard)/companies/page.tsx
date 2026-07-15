"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useCompanySearch } from "@/lib/hooks/companyQueries"
import { useCreateCompany } from "@/lib/hooks/mutationHooks"
import { useDebounce } from "@salesos/hooks"
import { Table, Input, Badge, Button, Spinner, Select, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter } from "@salesos/ui"
import { Search, Plus, Building2, ArrowLeft, ChevronLeft, ChevronRight, Loader2, MapPin, Hash } from "lucide-react"
import { ErrorFallback } from "@/components/foundation/error-boundary"
import type { ColumnDef } from "@tanstack/react-table"
import type { Company } from "@/lib/api"

const STATUS_OPTIONS = [
  { label: "الكل", value: "" },
  { label: "نشط", value: "active" },
  { label: "غير نشط", value: "inactive" },
  { label: "معلق", value: "suspended" },
  { label: "منتهي", value: "expired" },
]

const STATUS_VARIANT: Record<string, "success" | "warning" | "danger" | "default"> = {
  active: "success",
  inactive: "default",
  suspended: "warning",
  expired: "danger",
}

export default function CompaniesPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [formData, setFormData] = useState({ name_ar: "", cr_number: "", name_en: "", city: "", region: "" })
  const debouncedQuery = useDebounce(searchQuery, 400)

  const params: Record<string, unknown> = { page, page_size: 20 }
  if (debouncedQuery) params.q = debouncedQuery
  if (statusFilter) params.status = statusFilter

  const { data, isLoading, isError, error, refetch } = useCompanySearch(params)
  const createCompany = useCreateCompany()

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1

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
      setFormData({ name_ar: "", cr_number: "", name_en: "", city: "", region: "" })
      setPage(1)
    } catch {
    }
  }, [formData, createCompany])

  const columns: ColumnDef<Company>[] = [
    {
      accessorKey: "name_ar",
      header: "اسم الشركة",
      cell: ({ row }) => (
        <Link
          href={`/companies/${row.original.id}`}
          className="flex items-center gap-2 font-medium text-[var(--muhide-orange)] hover:underline dark:text-orange-400"
        >
          <Building2 className="h-4 w-4 shrink-0" />
          <span className="truncate">{row.original.name_ar || row.original.name_en}</span>
        </Link>
      ),
    },
    {
      accessorKey: "cr_number",
      header: "رقم السجل",
      cell: ({ getValue }) => (
        <span className="inline-flex items-center gap-1 text-sm text-neutral-600 dark:text-neutral-400">
          <Hash className="h-3 w-3 shrink-0 text-neutral-400" />
          {getValue() as string}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ getValue }) => {
        const status = getValue() as string
        return <Badge variant={STATUS_VARIANT[status] || "default"}>{status}</Badge>
      },
    },
    {
      accessorKey: "city",
      header: "المدينة",
      cell: ({ getValue }) => {
        const city = getValue() as string | null
        return city ? (
          <span className="inline-flex items-center gap-1 text-sm text-neutral-600 dark:text-neutral-400">
            <MapPin className="h-3 w-3 shrink-0 text-neutral-400" />
            {city}
          </span>
        ) : (
          <span className="text-neutral-400">-</span>
        )
      },
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <Link
          href={`/companies/${row.original.id}`}
          className="inline-flex items-center gap-1 text-sm text-[var(--muhide-orange)] hover:underline dark:text-orange-400"
        >
          التفاصيل
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
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">الشركات</h1>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            إدارة ومراقبة الشركات المسجلة في المنصة
          </p>
        </div>
        <Modal open={modalOpen} onOpenChange={setModalOpen}>
          <ModalTrigger>
            <Button leftIcon={<Plus className="h-4 w-4" />}>إضافة شركة</Button>
          </ModalTrigger>
          <ModalContent>
            <ModalHeader>إضافة شركة جديدة</ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">اسم الشركة (عربي) *</label>
                  <Input value={formData.name_ar} onChange={(e) => setFormData({ ...formData, name_ar: e.target.value })} placeholder="شركة الأمل للتجارة" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">رقم السجل التجاري *</label>
                  <Input value={formData.cr_number} onChange={(e) => setFormData({ ...formData, cr_number: e.target.value })} placeholder="١٢٣٤٥٦٧٨٩٠" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">اسم الشركة (إنجليزي)</label>
                  <Input value={formData.name_en} onChange={(e) => setFormData({ ...formData, name_en: e.target.value })} placeholder="Al Amal Trading Co." />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">المدينة</label>
                    <Input value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} placeholder="الرياض" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300">المنطقة</label>
                    <Input value={formData.region} onChange={(e) => setFormData({ ...formData, region: e.target.value })} placeholder="منطقة الرياض" />
                  </div>
                </div>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="outline" onClick={() => setModalOpen(false)}>إلغاء</Button>
              <Button onClick={handleCreate} disabled={!formData.name_ar || !formData.cr_number || createCompany.isPending} leftIcon={createCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
                {createCompany.isPending ? "جارٍ الحفظ..." : "حفظ"}
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <Input
          placeholder="البحث باسم الشركة أو رقم السجل التجاري..."
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
          leftIcon={<Search className="h-4 w-4" />}
          className="flex-1"
        />
        <div className="w-44">
          <Select
            options={STATUS_OPTIONS}
            placeholder="الحالة"
            value={statusFilter}
            onChange={(v) => { setStatusFilter(v); setPage(1) }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900">
        {isError ? (
          <div className="px-4 py-12">
            <ErrorFallback
              title="فشل تحميل البيانات"
              message={(error as Error)?.message || "تأكد من تشغيل الخادم الخلفي"}
              onRetry={() => refetch()}
              showDetails={process.env.NODE_ENV === "development"}
              errorDetails={String(error)}
            />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Building2 className="mb-3 h-10 w-10 text-neutral-300" />
            <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {searchQuery || statusFilter ? "لا توجد نتائج للبحث" : "لا توجد شركات"}
            </p>
            <p className="mt-1 text-sm text-neutral-500">
              {searchQuery || statusFilter ? "جرب تغيير معايير البحث" : "قم بإضافة أول شركة للبدء."}
            </p>
            {!searchQuery && !statusFilter && (
              <Button className="mt-4" onClick={() => setModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
                إضافة شركة
              </Button>
            )}
          </div>
        ) : (
          <Table<Company>
            columns={columns}
            data={data.items}
            loading={isLoading}
            onRowClick={(row) => router.push(`/companies/${row.id}`)}
          />
        )}
      </div>

      {/* Pagination */}
      {data && data.total > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            إجمالي {data.total} شركة — صفحة {page} من {totalPages}
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
                  variant={p === page ? "primary" : "outline"}
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
    </div>
  )
}
