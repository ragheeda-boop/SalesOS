"use client"

import { useState, useCallback } from"react"
import { useParams, useRouter } from"next/navigation"
import Link from"next/link"
import { CompanyWorkspace } from"@/components/company-workspace"
import { DecisionProvider } from"@/features/revenue-execution/_providers/DecisionProvider"
import { useCompany } from"@/lib/hooks/companyQueries"
import { useUpdateCompany, useDeleteCompany, useAddContact } from"@/lib/hooks/mutationHooks"
import { Button, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, Input } from"@salesos/ui"
import { Pencil, Trash2, UserPlus, ArrowRight, Loader2, BarChart3 } from"lucide-react"
import { ErrorBoundary } from"@/components/error-boundary"
import { ErrorFallback } from"@/components/foundation/error-boundary"
import { useTranslation } from"@/lib/i18n"

export default function CompanyPage() {
 const params = useParams()
 const router = useRouter()
 const id = params.id as string
 const { t } = useTranslation()

 const { data: company, isLoading, isError, error, refetch } = useCompany(id)
 const updateCompany = useUpdateCompany()
 const deleteCompany = useDeleteCompany()
 const addContact = useAddContact()

 const [editOpen, setEditOpen] = useState(false)
 const [deleteOpen, setDeleteOpen] = useState(false)
 const [contactOpen, setContactOpen] = useState(false)

 const [editForm, setEditForm] = useState({ name_ar:"", name_en:"", city:"", region:"" })
 const [contactForm, setContactForm] = useState({ name:"", position:"", email:"", phone:"" })

 const handleEditOpen = useCallback(() => {
 if (company) {
 setEditForm({
 name_ar: company.name_ar ||"",
 name_en: company.name_en ||"",
 city: company.city ||"",
 region: company.region ||"",
 })
 setEditOpen(true)
 }
 }, [company])

 const handleEditSave = useCallback(async () => {
 await updateCompany.mutateAsync({ id, ...editForm })
 setEditOpen(false)
 }, [id, editForm, updateCompany])

 const handleDelete = useCallback(async () => {
 await deleteCompany.mutateAsync({ id })
 setDeleteOpen(false)
 router.push("/companies")
 }, [id, deleteCompany, router])

 const handleAddContact = useCallback(async () => {
 if (!contactForm.name) return
 await addContact.mutateAsync({ companyId: id, ...contactForm })
 setContactOpen(false)
 setContactForm({ name:"", position:"", email:"", phone:"" })
 }, [id, contactForm, addContact])

 return (
 <div>
 <div className="mb-4 flex items-center justify-between">
 <Link
 href="/companies"
 className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] dark:hover:text-[var(--text-primary)] transition-colors"
 >
 <ArrowRight className="h-4 w-4" />
 {t("companies.back_to_list")}
 </Link>
 <div className="flex items-center gap-2">
 <Link href={`/companies/${id}/360`}>
 <Button variant="primary" size="sm" leftIcon={<BarChart3 className="h-4 w-4" />}>360 View</Button>
 </Link>
 <Modal open={contactOpen} onOpenChange={setContactOpen}>
 <ModalTrigger>
 <Button variant="outline" size="sm" leftIcon={<UserPlus className="h-4 w-4" />}>{t("companies.add_contact")}</Button>
 </ModalTrigger>
 <ModalContent>
 <ModalHeader>{t("companies.add_contact")}</ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.name")} *</label>
 <Input value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })} placeholder="Ahmed Mohammed" />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.position")}</label>
 <Input value={contactForm.position} onChange={(e) => setContactForm({ ...contactForm, position: e.target.value })} placeholder="Sales Manager" />
 </div>
 <div className="grid grid-cols-2 gap-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.email")}</label>
 <Input value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} placeholder="ahmed@example.com" />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.phone")}</label>
 <Input value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} placeholder="0512345678" />
 </div>
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setContactOpen(false)}>{t("common.cancel")}</Button>
 <Button onClick={handleAddContact} disabled={!contactForm.name || addContact.isPending} leftIcon={addContact.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {addContact.isPending ? t("common.saving") : t("common.save")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 <Button variant="outline" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={handleEditOpen}>{t("common.edit")}</Button>

 <Button variant="danger" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setDeleteOpen(true)}>{t("common.delete")}</Button>
 </div>
 </div>

  <ErrorBoundary fallback={<ErrorFallback title="تعذر تحميل لوحة الشركة" message="حدث خطأ غير متوقع. حاول مرة أخرى." />}>
    <DecisionProvider>
      <CompanyWorkspace companyId={id} />
    </DecisionProvider>
  </ErrorBoundary>

 <Modal open={editOpen} onOpenChange={setEditOpen}>
 <ModalContent>
 <ModalHeader>{t("companies.edit_title")}</ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("companies.name_ar")}</label>
 <Input value={editForm.name_ar} onChange={(e) => setEditForm({ ...editForm, name_ar: e.target.value })} />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("companies.name_en")}</label>
 <Input value={editForm.name_en} onChange={(e) => setEditForm({ ...editForm, name_en: e.target.value })} />
 </div>
 <div className="grid grid-cols-2 gap-4">
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.city")}</label>
 <Input value={editForm.city} onChange={(e) => setEditForm({ ...editForm, city: e.target.value })} />
 </div>
 <div>
 <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">{t("labels.region")}</label>
 <Input value={editForm.region} onChange={(e) => setEditForm({ ...editForm, region: e.target.value })} />
 </div>
 </div>
 </div>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setEditOpen(false)}>{t("common.cancel")}</Button>
 <Button onClick={handleEditSave} disabled={updateCompany.isPending} leftIcon={updateCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {updateCompany.isPending ? t("common.saving") : t("settings.save_changes")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>

 <Modal open={deleteOpen} onOpenChange={setDeleteOpen}>
 <ModalContent>
 <ModalHeader>{t("companies.confirm_delete_title")}</ModalHeader>
 <ModalBody>
 <p className="text-sm text-[var(--text-secondary)]">
 {t("companies.confirm_delete_message", { name: company?.name_ar || company?.name_en ||"" })}
 {""}{t("companies.delete_irreversible")}
 </p>
 </ModalBody>
 <ModalFooter>
 <Button variant="outline" onClick={() => setDeleteOpen(false)}>{t("common.cancel")}</Button>
 <Button variant="danger" onClick={handleDelete} disabled={deleteCompany.isPending} leftIcon={deleteCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
 {deleteCompany.isPending ? t("common.deleting") : t("companies.confirm_delete_title")}
 </Button>
 </ModalFooter>
 </ModalContent>
 </Modal>
 </div>
 )
}
