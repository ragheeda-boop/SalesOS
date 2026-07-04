"use client"

import { useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { CompanyWorkspace } from "@/components/company-workspace"
import { useCompany } from "@/lib/hooks/companyQueries"
import { useUpdateCompany, useDeleteCompany, useAddContact } from "@/lib/hooks/mutationHooks"
import { Button, Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter, Input, Spinner } from "@salesos/ui"
import { Pencil, Trash2, UserPlus, Loader2, ArrowLeft } from "lucide-react"

export default function CompanyPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const { data: company, isLoading } = useCompany(id)
  const updateCompany = useUpdateCompany()
  const deleteCompany = useDeleteCompany()
  const addContact = useAddContact()

  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [contactOpen, setContactOpen] = useState(false)

  const [editForm, setEditForm] = useState({ name_ar: "", name_en: "", city: "", region: "" })
  const [contactForm, setContactForm] = useState({ name: "", position: "", email: "", phone: "" })

  const handleEditOpen = useCallback(() => {
    if (company) {
      setEditForm({
        name_ar: company.name_ar || "",
        name_en: company.name_en || "",
        city: company.city || "",
        region: company.region || "",
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
    setContactForm({ name: "", position: "", email: "", phone: "" })
  }, [id, contactForm, addContact])

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <Link
          href="/companies"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
        >
          <ArrowLeft className="h-4 w-4" />
          العودة إلى الشركات
        </Link>
        <div className="flex items-center gap-2">
          <Modal open={contactOpen} onOpenChange={setContactOpen}>
            <ModalTrigger>
              <Button variant="outline" size="sm" leftIcon={<UserPlus className="h-4 w-4" />}>إضافة جهة اتصال</Button>
            </ModalTrigger>
            <ModalContent>
              <ModalHeader>إضافة جهة اتصال</ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">الاسم *</label>
                    <Input value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })} placeholder="أحمد محمد" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">المسمى الوظيفي</label>
                    <Input value={contactForm.position} onChange={(e) => setContactForm({ ...contactForm, position: e.target.value })} placeholder="مدير مبيعات" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">البريد الإلكتروني</label>
                      <Input value={contactForm.email} onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })} placeholder="ahmed@example.com" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">رقم الجوال</label>
                      <Input value={contactForm.phone} onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })} placeholder="0512345678" />
                    </div>
                  </div>
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="outline" onClick={() => setContactOpen(false)}>إلغاء</Button>
                <Button onClick={handleAddContact} disabled={!contactForm.name || addContact.isPending} leftIcon={addContact.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
                  {addContact.isPending ? "جارٍ الحفظ..." : "حفظ"}
                </Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

          <Button variant="outline" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={handleEditOpen}>تعديل</Button>

          <Button variant="danger" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setDeleteOpen(true)}>حذف</Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner className="h-6 w-6" /></div>
      ) : (
        <CompanyWorkspace companyId={id} />
      )}

      <Modal open={editOpen} onOpenChange={setEditOpen}>
        <ModalContent>
          <ModalHeader>تعديل بيانات الشركة</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة (عربي)</label>
                <Input value={editForm.name_ar} onChange={(e) => setEditForm({ ...editForm, name_ar: e.target.value })} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة (إنجليزي)</label>
                <Input value={editForm.name_en} onChange={(e) => setEditForm({ ...editForm, name_en: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">المدينة</label>
                  <Input value={editForm.city} onChange={(e) => setEditForm({ ...editForm, city: e.target.value })} />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">المنطقة</label>
                  <Input value={editForm.region} onChange={(e) => setEditForm({ ...editForm, region: e.target.value })} />
                </div>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>إلغاء</Button>
            <Button onClick={handleEditSave} disabled={updateCompany.isPending} leftIcon={updateCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
              {updateCompany.isPending ? "جارٍ الحفظ..." : "حفظ التغييرات"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal open={deleteOpen} onOpenChange={setDeleteOpen}>
        <ModalContent>
          <ModalHeader>تأكيد الحذف</ModalHeader>
          <ModalBody>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              هل أنت متأكد من حذف شركة <strong>{company?.name_ar || company?.name_en}</strong>؟
              هذا الإجراء لا يمكن التراجع عنه.
            </p>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>إلغاء</Button>
            <Button variant="danger" onClick={handleDelete} disabled={deleteCompany.isPending} leftIcon={deleteCompany.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : undefined}>
              {deleteCompany.isPending ? "جارٍ الحذف..." : "تأكيد الحذف"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  )
}
