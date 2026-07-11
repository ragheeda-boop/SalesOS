"use client"

import { useState } from "react"
import { useRagDocuments, useIngestDocument, useDeleteDocument, type DocumentSourceType } from "@/lib/ragQueries"

const SOURCE_LABELS: Record<DocumentSourceType, string> = {
  email: "بريد",
  meeting: "اجتماع",
  note: "ملاحظة",
}

const SOURCE_COLORS: Record<DocumentSourceType, string> = {
  email: "bg-info-100 text-info-700",
  meeting: "bg-success-100 text-success-700",
  note: "bg-warning-100 text-warning-700",
}

export function RagDocumentManager() {
  const { data: documents, isLoading, error } = useRagDocuments()
  const ingestDocument = useIngestDocument()
  const deleteDocument = useDeleteDocument()

  const [showIngest, setShowIngest] = useState(false)
  const [title, setTitle] = useState("")
  const [content, setContent] = useState("")
  const [sourceType, setSourceType] = useState<DocumentSourceType>("note")
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const handleIngest = async () => {
    if (!title.trim() || !content.trim()) return
    await ingestDocument.mutateAsync({ title: title.trim(), content: content.trim(), source_type: sourceType })
    setTitle("")
    setContent("")
    setSourceType("note")
    setShowIngest(false)
  }

  const handleDelete = async (id: string) => {
    await deleteDocument.mutateAsync(id)
    setDeleteConfirm(null)
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden">
      <div className="flex items-center justify-between border-b border-[var(--border-default)] px-4 py-3">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">المستندات</h2>
        <button onClick={() => setShowIngest(true)} className="rounded-lg bg-[var(--muhide-orange)] px-2 py-1 text-xs text-white hover:opacity-90">
          + إضافة
        </button>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-2">
        {isLoading && (
          <div className="space-y-2 animate-pulse">
            <div className="h-12 bg-neutral-100 rounded-lg" />
            <div className="h-12 bg-neutral-100 rounded-lg" />
            <div className="h-12 bg-neutral-100 rounded-lg" />
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-sm text-danger-600">فشل تحميل المستندات</p>
          </div>
        )}

        {!isLoading && !error && (!documents || documents.length === 0) && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-[var(--text-muted)]">لا توجد مستندات</p>
              <button onClick={() => setShowIngest(true)} className="mt-2 text-xs text-[var(--muhide-orange)] hover:underline">
                إضافة مستند جديد
              </button>
            </div>
          </div>
        )}

        {documents?.map((doc) => (
          <div key={doc.id} className="rounded-lg border border-[var(--border-default)] p-3 space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-sm font-medium text-[var(--text-primary)] truncate">{doc.title}</span>
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${SOURCE_COLORS[doc.source_type] || SOURCE_COLORS.note}`}>
                  {SOURCE_LABELS[doc.source_type]}
                </span>
              </div>
              {deleteConfirm === doc.id ? (
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => handleDelete(doc.id)} disabled={deleteDocument.isPending} className="text-xs text-danger-600 hover:underline">
                    {deleteDocument.isPending ? "..." : "تأكيد"}
                  </button>
                  <button onClick={() => setDeleteConfirm(null)} className="text-xs text-[var(--text-muted)] hover:underline">إلغاء</button>
                </div>
              ) : (
                <button onClick={() => setDeleteConfirm(doc.id)} className="text-xs text-[var(--text-muted)] hover:text-danger-600 shrink-0">حذف</button>
              )}
            </div>
            <p className="text-xs text-[var(--text-secondary)] line-clamp-2">{doc.content}</p>
            <p className="text-[10px] text-[var(--text-muted)]">{new Date(doc.created_at).toLocaleDateString("ar-SA")}</p>
          </div>
        ))}
      </div>

      {showIngest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-[var(--bg-primary)] p-6 shadow-xl space-y-4 m-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-[var(--text-primary)]">إضافة مستند</h3>
              <button onClick={() => setShowIngest(false)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">✕</button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">العنوان</label>
                <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">المحتوى</label>
                <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={4} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">المصدر</label>
                <select value={sourceType} onChange={(e) => setSourceType(e.target.value as DocumentSourceType)} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]">
                  <option value="note">ملاحظة</option>
                  <option value="email">بريد</option>
                  <option value="meeting">اجتماع</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={() => setShowIngest(false)} className="rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-muted)]">إلغاء</button>
              <button onClick={handleIngest} disabled={!title.trim() || !content.trim() || ingestDocument.isPending} className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-sm text-white hover:opacity-90 disabled:opacity-50">
                {ingestDocument.isPending ? "جاري..." : "إضافة"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
