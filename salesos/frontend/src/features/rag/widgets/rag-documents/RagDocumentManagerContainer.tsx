"use client"

import { useState } from "react"
import { useRagDocuments, useIngestDocument, useDeleteDocument, type DocumentSourceType } from "@/lib/ragQueries"
import { RagDocumentManagerView } from "./RagDocumentManagerView"

export function RagDocumentManagerContainer() {
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
    <RagDocumentManagerView
      documents={documents}
      isLoading={isLoading}
      error={!!error}
      showIngest={showIngest}
      setShowIngest={setShowIngest}
      title={title}
      setTitle={setTitle}
      content={content}
      setContent={setContent}
      sourceType={sourceType}
      setSourceType={setSourceType}
      deleteConfirm={deleteConfirm}
      setDeleteConfirm={setDeleteConfirm}
      onIngest={handleIngest}
      onDelete={handleDelete}
      isIngesting={ingestDocument.isPending}
      isDeleting={deleteDocument.isPending}
    />
  )
}
