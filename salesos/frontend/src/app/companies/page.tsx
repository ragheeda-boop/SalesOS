"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { useCompanySearch } from "@/lib/hooks/companyQueries"
import { useCreateCompany } from "@/lib/hooks/mutationHooks"
import { useDebounce } from "@salesos/hooks"
import { Input, Badge, Button, Spinner, Select, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter } from "@salesos/ui"
import { Search, Plus, Building2, ArrowLeft, ChevronLeft, ChevronRight, Loader2 } from "lucide-react"

const STATUS_OPTIONS = [
  { label: "الكل", value: "" },
  { label: "نشط", value: "active" },
  { label: "غير نشط", value: "inactive" },
  { label: "معلق", value: "suspended" },
  { label: "منتهي", value: "expired" },
]

export default function CompaniesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [formData, setFormData] = useState({ name_ar: "", cr_number: "", name_en: "", city: "", region: "" })
  const debouncedQuery = useDebounce(searchQuery, 400)

  const params: Record<string, unknown> = { page, page_size: 20 }
  if (debouncedQuery) params.q = debouncedQuery
  if (statusFilter) params.status = statusFilter

  const { data, isLoading, isError } = useCompanySearch(params)
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الشركات</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
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
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة (عربي) *</label>
                  <Input value={formData.name_ar} onChange={(e) => setFormData({ ...formData, name_ar: e.target.value })} placeholder="شركة الأمل للتجارة" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">رقم السجل التجاري *</label>
                  <Input value={formData.cr_number} onChange={(e) => setFormData({ ...formData, cr_number: e.target.value })} placeholder="١٢٣٤٥٦٧٨٩٠" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة (إنجليزي)</label>
                  <Input value={formData.name_en} onChange={(e) => setFormData({ ...formData, name_en: e.target.value })} placeholder="Al Amal Trading Co." />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">المدينة</label>
                    <Input value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} placeholder="الرياض" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">المنطقة</label>
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

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">رقم السجل</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">الحالة</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">المدينة</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                  <div className="flex items-center justify-center gap-2">
                    <Spinner className="h-5 w-5" />
                    <span>جاري التحميل...</span>
                  </div>
                </td>
              </tr>
            ) : isError ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-red-500">فشل تحميل البيانات</td>
              </tr>
            ) : !data || data.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery || statusFilter ? "لا توجد نتائج للبحث" : "لا توجد شركات. قم بإضافة أول شركة للبدء."}
                </td>
              </tr>
            ) : (
              data.items.map((company) => (
                <tr key={company.id} className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3">
                    <Link href={`/companies/${company.id}`} className="flex items-center gap-2 font-medium text-blue-600 hover:underline dark:text-blue-400">
                      <Building2 className="h-4 w-4" />
                      {company.name_ar || company.name_en}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{company.cr_number}</td>
                  <td className="px-4 py-3">
                    <Badge variant="primary">{company.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{company.city || "-"}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/companies/${company.id}`}
                      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400"
                    >
                      عرض التفاصيل
                      <ArrowLeft className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && data.total > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500 dark:text-gray-400">
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
