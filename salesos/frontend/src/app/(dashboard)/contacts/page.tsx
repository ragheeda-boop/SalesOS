"use client"

import { useState, useCallback } from "react"
import { useContactSearch, useCreateContact, useUpdateContact, useDeleteContact } from "@/lib/hooks/contactQueries"
import { useCompanySearch } from "@/lib/hooks/companyQueries"
import { useDebounce } from "@salesos/hooks"
import { Input, Badge, Button, Spinner, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, useToast } from "@salesos/ui"
import { Search, Plus, Users, ChevronLeft, ChevronRight, Pencil, Trash2, X, Loader2, Building2 } from "lucide-react"
import Link from "next/link"
import type { Contact, Company } from "@/lib/api"
import type { AxiosError } from "axios"

export default function ContactsPage() {
  const { toast } = useToast()
  const [searchQuery, setSearchQuery] = useState("")
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [formData, setFormData] = useState({
    name: "", email: "", phone: "", mobile: "", position: "", department: "", source: "", company_id: "", tags: "",
  })
  const [companySearch, setCompanySearch] = useState("")
  const [selectedCompany, setSelectedCompany] = useState<{ id: string; name: string } | null>(null)

  const debouncedQuery = useDebounce(searchQuery, 400)

  const params: Record<string, unknown> = { page, page_size: 20 }
  if (debouncedQuery) params.q = debouncedQuery

  const { data, isLoading, isError } = useContactSearch(params)
  const createContact = useCreateContact()
  const updateContact = useUpdateContact()
  const deleteContact = useDeleteContact()
  const { data: companyResults } = useCompanySearch({ q: companySearch, page: 1, page_size: 10 })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1

  const resetForm = () => {
    setFormData({ name: "", email: "", phone: "", mobile: "", position: "", department: "", source: "", company_id: "", tags: "" })
    setSelectedCompany(null)
    setCompanySearch("")
  }

  const handleCreate = useCallback(async () => {
    if (!formData.name.trim()) return
    try {
      await createContact.mutateAsync({
        name: formData.name.trim(),
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        mobile: formData.mobile || undefined,
        position: formData.position || undefined,
        department: formData.department || undefined,
        source: formData.source || undefined,
        company_id: selectedCompany?.id || undefined,
        tags: formData.tags ? formData.tags.split(",").map(t => t.trim()).filter(Boolean) : undefined,
      })
      setCreateOpen(false)
      resetForm()
      setPage(1)
      toast({ variant: "success", title: "تمت الإضافة", description: "تم إضافة جهة الاتصال بنجاح" })
    } catch (err: unknown) {
      const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
      toast({ variant: "error", title: "فشل الإضافة", description: detail || "حدث خطأ أثناء إضافة جهة الاتصال" })
    }
  }, [formData, selectedCompany, createContact, toast])

  const handleEdit = useCallback(async () => {
    if (!selectedContact || !formData.name.trim()) return
    try {
      await updateContact.mutateAsync({
        id: selectedContact.id,
        name: formData.name.trim(),
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        mobile: formData.mobile || undefined,
        position: formData.position || undefined,
        department: formData.department || undefined,
      })
      setEditOpen(false)
      setSelectedContact(null)
      toast({ variant: "success", title: "تم التعديل", description: "تم تعديل جهة الاتصال بنجاح" })
    } catch (err: unknown) {
      const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
      toast({ variant: "error", title: "فشل التعديل", description: detail || "حدث خطأ أثناء تعديل جهة الاتصال" })
    }
  }, [selectedContact, formData, updateContact, toast])

  const handleDelete = useCallback(async () => {
    if (!selectedContact) return
    try {
      await deleteContact.mutateAsync({ id: selectedContact.id })
      setDeleteOpen(false)
      setSelectedContact(null)
      toast({ variant: "success", title: "تم الحذف", description: "تم حذف جهة الاتصال بنجاح" })
    } catch (err: unknown) {
      const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
      toast({ variant: "error", title: "فشل الحذف", description: detail || "حدث خطأ أثناء حذف جهة الاتصال" })
    }
  }, [selectedContact, deleteContact, toast])

  const openEdit = (contact: Contact) => {
    const c = contact
    setSelectedContact({
      id: c.id, name: c.name, email: c.email ?? null, phone: c.phone ?? null,
      position: c.position ?? null, mobile: c.mobile ?? null, department: c.department ?? null,
      company_id: c.company_id ?? null, source: c.source ?? null, tags: c.tags ?? [],
    })
    setFormData({
      name: c.name ?? "", email: c.email ?? "", phone: c.phone ?? "", mobile: c.mobile ?? "",
      position: c.position ?? "", department: c.department ?? "", source: c.source ?? "",
      company_id: c.company_id ?? "", tags: Array.isArray(c.tags) ? c.tags.join(", ") : "",
    })
    setEditOpen(true)
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">جهات الاتصال</h1>
          <p className="text-sm text-neutral-500">
            {data ? `إجمالي ${data.total} جهة اتصال` : ""}
          </p>
        </div>
        <Modal open={createOpen} onOpenChange={(o: boolean) => { setCreateOpen(o); if (!o) resetForm() }}>
          <ModalTrigger asChild>
            <Button size="sm">
              <Plus className="ml-1 h-4 w-4" />
              جهة اتصال جديدة
            </Button>
          </ModalTrigger>
          <ModalContent>
            <ModalHeader>إضافة جهة اتصال</ModalHeader>
            <ModalBody>
              <div className="flex flex-col gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">الاسم *</label>
                  <Input value={formData.name} onChange={(e) => setFormData(p => ({ ...p, name: e.target.value }))} placeholder="الاسم الكامل" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-neutral-600">البريد الإلكتروني</label>
                    <Input value={formData.email} onChange={(e) => setFormData(p => ({ ...p, email: e.target.value }))} placeholder="email@example.com" />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-neutral-600">رقم الجوال</label>
                    <Input value={formData.phone} onChange={(e) => setFormData(p => ({ ...p, phone: e.target.value }))} placeholder="05xxxxxxxx" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-neutral-600">المنصب</label>
                    <Input value={formData.position} onChange={(e) => setFormData(p => ({ ...p, position: e.target.value }))} placeholder="المسمى الوظيفي" />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-neutral-600">القسم</label>
                    <Input value={formData.department} onChange={(e) => setFormData(p => ({ ...p, department: e.target.value }))} placeholder="القسم" />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">الشركة</label>
                  {selectedCompany ? (
                    <div className="flex items-center justify-between rounded-md border border-neutral-200 bg-white px-3 py-2 text-sm">
                      <span>{selectedCompany.name}</span>
                      <button onClick={() => { setSelectedCompany(null); setCompanySearch("") }} className="text-neutral-400 hover:text-danger-500"><X className="h-4 w-4" /></button>
                    </div>
                  ) : (
                    <>
                      <Input placeholder="ابحث عن شركة..." value={companySearch} onChange={(e) => setCompanySearch(e.target.value)} className="mb-1" />
                      {companyResults?.items && companyResults.items.length > 0 && (
                        <div className="max-h-40 overflow-y-auto rounded-md border border-neutral-200 bg-white">
                          {companyResults.items.slice(0, 6).map((c: Company) => (
                            <button key={c.id} onClick={() => setSelectedCompany({ id: c.id, name: c.name_ar })} className="w-full px-3 py-1.5 text-right text-sm hover:bg-neutral-100">
                              {c.name_ar}
                              {c.cr_number && <span className="mr-2 text-xs text-neutral-400">{c.cr_number}</span>}
                            </button>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">المصدر</label>
                  <Input value={formData.source} onChange={(e) => setFormData(p => ({ ...p, source: e.target.value }))} placeholder="مصدر جهة الاتصال" />
                </div>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>إلغاء</Button>
              <Button onClick={handleCreate} disabled={!formData.name.trim() || createContact.isPending}>
                {createContact.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                حفظ
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>

      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <Input
            placeholder="بحث عن جهة اتصال..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
            className="pr-10"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
        {isLoading ? (
          <div className="flex items-center justify-center py-20"><Spinner className="h-8 w-8" /></div>
        ) : isError ? (
          <div className="py-20 text-center text-danger-500">فشل تحميل جهات الاتصال</div>
        ) : !data?.items.length ? (
          <div className="flex flex-col items-center justify-center py-20 text-neutral-400">
            <Users className="mb-3 h-12 w-12" />
            <p>لا توجد جهات اتصال</p>
          </div>
        ) : (
          <table className="w-full text-right responsive-table">
            <thead className="border-b border-neutral-200 bg-neutral-50 text-xs font-medium text-neutral-500">
              <tr>
                <th className="px-4 py-3">الاسم</th>
                <th className="px-4 py-3">البريد الإلكتروني</th>
                <th className="px-4 py-3">رقم الجوال</th>
                <th className="px-4 py-3">المنصب</th>
                <th className="px-4 py-3">القسم</th>
                <th className="px-4 py-3">الشركة</th>
                <th className="px-4 py-3">المصدر</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {data.items.map((contact: Contact) => (
                <tr key={contact.id} className="text-sm text-neutral-700 hover:bg-neutral-50">
                  <td className="px-4 py-3 font-medium text-neutral-900" data-label="الاسم">{contact.name}</td>
                  <td className="px-4 py-3" data-label="البريد الإلكتروني">{contact.email || <span className="text-neutral-400">—</span>}</td>
                  <td className="px-4 py-3" data-label="رقم الجوال">{contact.phone || <span className="text-neutral-400">—</span>}</td>
                  <td className="px-4 py-3" data-label="المنصب">{contact.position || <span className="text-neutral-400">—</span>}</td>
                  <td className="px-4 py-3" data-label="القسم">{contact.department || <span className="text-neutral-400">—</span>}</td>
                  <td className="px-4 py-3" data-label="الشركة">
                    {contact.company_id ? (
                      <Link href={`/companies/${contact.company_id}`} className="flex items-center gap-1 text-[var(--muhide-orange)] hover:underline">
                        <Building2 className="h-3 w-3" />
                        <span>{contact.company_name || ""}</span>
                      </Link>
                    ) : <span className="text-neutral-400">—</span>}
                  </td>
                  <td className="px-4 py-3" data-label="المصدر">{contact.source || <span className="text-neutral-400">—</span>}</td>
                  <td className="px-4 py-3" data-label="">
                    <div className="flex items-center gap-1">
                      <button onClick={() => openEdit(contact)} className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-[var(--muhide-orange)]" title="تعديل">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button onClick={() => { setSelectedContact(contact); setDeleteOpen(true) }} className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-danger-600" title="حذف">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.total > 20 && (
        <div className="mt-4 flex items-center justify-between text-sm text-neutral-500">
          <span>صفحة {page} من {totalPages}</span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const start = Math.max(1, Math.min(page - 3, totalPages - 6))
              const p = start + i
              if (p > totalPages) return null
              return (
                <button key={p} onClick={() => setPage(p)} className={`h-8 w-8 rounded-md text-sm ${p === page ? "bg-[var(--muhide-orange)] text-white" : "text-neutral-600 hover:bg-neutral-100"}`}>
                  {p}
                </button>
              )
            })}
            <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      <Modal open={editOpen} onOpenChange={(o: boolean) => { setEditOpen(o); if (!o) setSelectedContact(null) }}>
        <ModalContent>
          <ModalHeader>تعديل جهة الاتصال</ModalHeader>
          <ModalBody>
            <div className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-neutral-600">الاسم *</label>
                <Input value={formData.name} onChange={(e) => setFormData(p => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">البريد الإلكتروني</label>
                  <Input value={formData.email} onChange={(e) => setFormData(p => ({ ...p, email: e.target.value }))} />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">رقم الجوال</label>
                  <Input value={formData.phone} onChange={(e) => setFormData(p => ({ ...p, phone: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">المنصب</label>
                  <Input value={formData.position} onChange={(e) => setFormData(p => ({ ...p, position: e.target.value }))} />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-neutral-600">القسم</label>
                  <Input value={formData.department} onChange={(e) => setFormData(p => ({ ...p, department: e.target.value }))} />
                </div>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={() => setEditOpen(false)}>إلغاء</Button>
            <Button onClick={handleEdit} disabled={!formData.name.trim() || updateContact.isPending}>
              {updateContact.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              حفظ التعديلات
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation */}
      <Modal open={deleteOpen} onOpenChange={(o: boolean) => { setDeleteOpen(o); if (!o) setSelectedContact(null) }}>
        <ModalContent>
          <ModalHeader>تأكيد الحذف</ModalHeader>
          <ModalBody>
            <p className="text-sm text-neutral-600">
              هل أنت متأكد من حذف <strong>{selectedContact?.name}</strong>؟
            </p>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={() => setDeleteOpen(false)}>إلغاء</Button>
            <Button onClick={handleDelete} disabled={deleteContact.isPending} className="bg-danger-600 hover:bg-danger-700">
              {deleteContact.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              حذف
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  )
}
