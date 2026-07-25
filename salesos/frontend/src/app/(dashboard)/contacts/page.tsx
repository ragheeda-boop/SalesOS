"use client"

import { useState, useCallback } from"react"
import { useContactSearch, useCreateContact, useUpdateContact, useDeleteContact } from"@/lib/hooks/contactQueries"
import { useCompanySearch } from"@/lib/hooks/companyQueries"
import { useDebounce } from"@salesos/hooks"
import { Input, Badge, Button, Spinner, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, useToast, Tooltip } from"@salesos/ui"
import { Search, Plus, Users, ChevronLeft, ChevronRight, Pencil, Trash2, X, Building2 } from"lucide-react"
import Link from"next/link"
import type { Contact, Company } from"@/lib/api"
import type { AxiosError } from"axios"
import { ErrorFallback } from"@/components/foundation/error-boundary"
import { useTranslation } from"@/lib/i18n"

export default function ContactsPage() {
 const { t } = useTranslation()
 const { toast } = useToast()
 const [searchQuery, setSearchQuery] = useState("")
 const [page, setPage] = useState(1)
 const [createOpen, setCreateOpen] = useState(false)
 const [editOpen, setEditOpen] = useState(false)
 const [deleteOpen, setDeleteOpen] = useState(false)
 const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
 const [formData, setFormData] = useState({
 name:"", email:"", phone:"", mobile:"", position:"", department:"", source:"", company_id:"", tags:"",
 })
 const [companySearch, setCompanySearch] = useState("")
 const [selectedCompany, setSelectedCompany] = useState<{ id: string; name: string } | null>(null)

 const debouncedQuery = useDebounce(searchQuery, 400)

 const params: Record<string, unknown> = { page, page_size: 20 }
 if (debouncedQuery) params.q = debouncedQuery

 const { data, isLoading, isError, error, refetch } = useContactSearch(params)
 const createContact = useCreateContact()
 const updateContact = useUpdateContact()
 const deleteContact = useDeleteContact()
 const { data: companyResults } = useCompanySearch({ q: companySearch, page: 1, page_size: 10 })

 const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1

 const resetForm = () => {
 setFormData({ name:"", email:"", phone:"", mobile:"", position:"", department:"", source:"", company_id:"", tags:"" })
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
 toast({ variant:"success", title: t("contacts.added"), description: t("contacts.added_desc") })
 } catch (err: unknown) {
 const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
 toast({ variant:"error", title: t("contacts.add_failed"), description: detail || t("contacts.add_error") })
 }
 }, [formData, selectedCompany, createContact, toast, t])

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
 toast({ variant:"success", title: t("contacts.updated"), description: t("contacts.updated_desc") })
 } catch (err: unknown) {
 const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
 toast({ variant:"error", title: t("contacts.update_failed"), description: detail || t("contacts.update_error") })
 }
 }, [selectedContact, formData, updateContact, toast, t])

 const handleDelete = useCallback(async () => {
 if (!selectedContact) return
 try {
 await deleteContact.mutateAsync({ id: selectedContact.id })
 setDeleteOpen(false)
 setSelectedContact(null)
 toast({ variant:"success", title: t("contacts.deleted"), description: t("contacts.deleted_desc") })
 } catch (err: unknown) {
 const detail = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail
 toast({ variant:"error", title: t("contacts.delete_failed"), description: detail || t("contacts.delete_error") })
 }
 }, [selectedContact, deleteContact, toast, t])

 const openEdit = (contact: Contact) => {
 const c = contact
 setSelectedContact({
 id: c.id, name: c.name, email: c.email ?? null, phone: c.phone ?? null,
 position: c.position ?? null, mobile: c.mobile ?? null, department: c.department ?? null,
 company_id: c.company_id ?? null, source: c.source ?? null, tags: c.tags ?? [],
 })
 setFormData({
 name: c.name ??"", email: c.email ??"", phone: c.phone ??"", mobile: c.mobile ??"",
 position: c.position ??"", department: c.department ??"", source: c.source ??"",
 company_id: c.company_id ??"", tags: Array.isArray(c.tags) ? c.tags.join(",") :"",
 })
 setEditOpen(true)
 }

 return (
 <div className="mx-auto max-w-7xl">
 <div className="mb-6 flex items-center justify-between">
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">{t("contacts.title")}</h1>
 <p className="text-sm text-[var(--text-muted)]">
 {data ? t("contacts.total", { count: data.total }) :""}
 </p>
 </div>
 <Modal open={createOpen} onOpenChange={(o: boolean) => { setCreateOpen(o); if (!o) resetForm() }}>
 <ModalTrigger asChild>
 <Button size="sm">
 <Plus className="ml-1 h-4 w-4" />
 {t("contacts.new")}
 </Button>
 </ModalTrigger>
 <ModalContent>
 <ModalHeader>{t("contacts.add")}</ModalHeader>
 <ModalBody>
 <div className="flex flex-col gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.name")}</label>
 <Input value={formData.name} onChange={(e) => setFormData(p => ({ ...p, name: e.target.value }))} placeholder={t("contacts.name_placeholder")} />
 </div>
 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.email")}</label>
 <Input value={formData.email} onChange={(e) => setFormData(p => ({ ...p, email: e.target.value }))} placeholder="email@example.com" />
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.phone")}</label>
 <Input value={formData.phone} onChange={(e) => setFormData(p => ({ ...p, phone: e.target.value }))} placeholder="05xxxxxxxx" />
 </div>
 </div>
 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.position")}</label>
 <Input value={formData.position} onChange={(e) => setFormData(p => ({ ...p, position: e.target.value }))} placeholder={t("contacts.position_placeholder")} />
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.department")}</label>
 <Input value={formData.department} onChange={(e) => setFormData(p => ({ ...p, department: e.target.value }))} placeholder={t("contacts.department")} />
 </div>
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.company")}</label>
 {selectedCompany ? (
 <div className="flex items-center justify-between rounded-md border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm">
 <span>{selectedCompany.name}</span>
 <button onClick={() => { setSelectedCompany(null); setCompanySearch("") }} className="text-[var(--text-disabled)] hover:text-danger-500"><X className="h-4 w-4" /></button>
 </div>
 ) : (
 <>
 <Input placeholder={t("contacts.company_search")} value={companySearch} onChange={(e) => setCompanySearch(e.target.value)} className="mb-1" />
 {companyResults?.items && companyResults.items.length > 0 && (
 <div className="max-h-40 overflow-y-auto rounded-md border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {companyResults.items.slice(0, 6).map((c: Company) => (
 <button key={c.id} onClick={() => setSelectedCompany({ id: c.id, name: c.name_ar })} className="w-full px-3 py-1.5 text-right text-sm hover:bg-[var(--bg-tertiary)]">
 {c.name_ar}
 {c.cr_number && <span className="mr-2 text-xs text-[var(--text-disabled)]">{c.cr_number}</span>}
 </button>
 ))}
 </div>
 )}
 </>
 )}
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.source")}</label>
 <Input value={formData.source} onChange={(e) => setFormData(p => ({ ...p, source: e.target.value }))} placeholder={t("contacts.source_placeholder")} />
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="ghost" onClick={() => setCreateOpen(false)}>{t("contacts.cancel")}</Button>
 <Button onClick={handleCreate} disabled={!formData.name.trim() || createContact.isPending}>
 {createContact.isPending ? <Spinner className="h-4 w-4" /> : null}
 {t("contacts.save")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>

 <div className="mb-4 flex items-center gap-3">
 <div className="relative flex-1">
 <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-disabled)]" />
 <Input
 placeholder={t("contacts.search_placeholder")}
 value={searchQuery}
 onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
 className="pr-10"
 />
 </div>
 </div>

 <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {isLoading ? (
 <div className="flex items-center justify-center py-20"><Spinner className="h-8 w-8" /></div>
 ) : isError ? (
 <ErrorFallback
 title={t("contacts.load_error")}
 message={(error as Error)?.message || t("contacts.load_error_hint")}
 onRetry={() => refetch()}
 showDetails={process.env.NODE_ENV ==="development"}
 errorDetails={String(error)}
 />
 ) : !data?.items.length ? (
 <div className="flex flex-col items-center justify-center py-20 text-[var(--text-disabled)]">
 <Users className="mb-3 h-12 w-12" />
 <p>{t("contacts.no_contacts")}</p>
 </div>
 ) : (
 <table className="w-full text-right responsive-table">
 <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-xs font-medium text-[var(--text-muted)]">
 <tr>
 <th className="px-4 py-3">{t("contacts.name")}</th>
 <th className="px-4 py-3">{t("contacts.email")}</th>
 <th className="px-4 py-3">{t("contacts.phone")}</th>
 <th className="px-4 py-3">{t("contacts.position")}</th>
 <th className="px-4 py-3">{t("contacts.department")}</th>
 <th className="px-4 py-3">{t("contacts.company")}</th>
 <th className="px-4 py-3">{t("contacts.source")}</th>
 <th className="px-4 py-3"></th>
 </tr>
 </thead>
 <tbody className="divide-y divide-neutral-100">
 {data.items.map((contact: Contact) => (
 <tr key={contact.id} className="text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]">
 <td className="px-4 py-3 font-medium text-[var(--text-primary)]" data-label={t("contacts.name")}>{contact.name}</td>
 <td className="px-4 py-3" data-label={t("contacts.email")}>{contact.email || <span className="text-[var(--text-disabled)]">—</span>}</td>
 <td className="px-4 py-3" data-label={t("contacts.phone")}>{contact.phone || <span className="text-[var(--text-disabled)]">—</span>}</td>
 <td className="px-4 py-3" data-label={t("contacts.position")}>{contact.position || <span className="text-[var(--text-disabled)]">—</span>}</td>
 <td className="px-4 py-3" data-label={t("contacts.department")}>{contact.department || <span className="text-[var(--text-disabled)]">—</span>}</td>
 <td className="px-4 py-3" data-label={t("contacts.company")}>
 {contact.company_id ? (
 <Link href={`/companies/${contact.company_id}`} className="flex items-center gap-1 text-[var(--muhide-orange)] hover:underline">
 <Building2 className="h-3 w-3" />
 <span>{contact.company_name ||""}</span>
 </Link>
 ) : <span className="text-[var(--text-disabled)]">—</span>}
 </td>
 <td className="px-4 py-3" data-label={t("contacts.source")}>{contact.source || <span className="text-[var(--text-disabled)]">—</span>}</td>
 <td className="px-4 py-3" data-label="">
 <div className="flex items-center gap-1">
 <Tooltip content={t("contacts.edit_tooltip")} side="top">
 <button onClick={() => openEdit(contact)} className="rounded p-1 text-[var(--text-disabled)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--muhide-orange)]">
 <Pencil className="h-4 w-4" />
 </button>
 </Tooltip>
 <Tooltip content={t("contacts.delete_tooltip")} side="top">
 <button onClick={() => { setSelectedContact(contact); setDeleteOpen(true) }} className="rounded p-1 text-[var(--text-disabled)] hover:bg-[var(--bg-tertiary)] hover:text-danger-600">
 <Trash2 className="h-4 w-4" />
 </button>
 </Tooltip>
 </div>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 )}
 </div>

 {data && data.total > 20 && (
 <div className="mt-4 flex items-center justify-between text-sm text-[var(--text-muted)]">
 <span>{t("contacts.page_of", { page, total: totalPages })}</span>
 <div className="flex items-center gap-2">
 <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
 <ChevronRight className="h-4 w-4" />
 </Button>
 {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
 const start = Math.max(1, Math.min(page - 3, totalPages - 6))
 const p = start + i
 if (p > totalPages) return null
 return (
 <button key={p} onClick={() => setPage(p)} className={`h-8 w-8 rounded-md text-sm ${p === page ?"bg-[var(--muhide-orange)] text-white" :"text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"}`}>
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
 <ModalHeader>{t("contacts.edit")}</ModalHeader>
 <ModalBody>
 <div className="flex flex-col gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.name")}</label>
 <Input value={formData.name} onChange={(e) => setFormData(p => ({ ...p, name: e.target.value }))} />
 </div>
 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.email")}</label>
 <Input value={formData.email} onChange={(e) => setFormData(p => ({ ...p, email: e.target.value }))} />
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.phone")}</label>
 <Input value={formData.phone} onChange={(e) => setFormData(p => ({ ...p, phone: e.target.value }))} />
 </div>
 </div>
 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.position")}</label>
 <Input value={formData.position} onChange={(e) => setFormData(p => ({ ...p, position: e.target.value }))} />
 </div>
 <div>
 <label className="mb-1 block text-xs font-medium text-[var(--text-secondary)]">{t("contacts.department")}</label>
 <Input value={formData.department} onChange={(e) => setFormData(p => ({ ...p, department: e.target.value }))} />
 </div>
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="ghost" onClick={() => setEditOpen(false)}>{t("contacts.cancel")}</Button>
 <Button onClick={handleEdit} disabled={!formData.name.trim() || updateContact.isPending}>
 {updateContact.isPending ? <Spinner className="h-4 w-4" /> : null}
 {t("contacts.save_changes")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 {/* Delete Confirmation */}
 <Modal open={deleteOpen} onOpenChange={(o: boolean) => { setDeleteOpen(o); if (!o) setSelectedContact(null) }}>
 <ModalContent>
 <ModalHeader>{t("contacts.delete_confirm")}</ModalHeader>
 <ModalBody>
 <p className="text-sm text-[var(--text-secondary)]">
 {t("contacts.delete_question")} <strong>{selectedContact?.name}</strong>?
 </p>
 </ModalBody>
 <ModalFooter>
 <Button variant="ghost" onClick={() => setDeleteOpen(false)}>{t("contacts.cancel")}</Button>
 <Button onClick={handleDelete} disabled={deleteContact.isPending} className="bg-danger-600 hover:bg-danger-700">
 {deleteContact.isPending ? <Spinner className="h-4 w-4" /> : null}
 {t("contacts.delete")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>
 )
}
