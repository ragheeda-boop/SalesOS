"use client"

import { MessageSquareText } from "lucide-react"
import { EmptyState } from "./EmptyState"

interface EmptyRAGProps {
  onUpload?: () => void
}

export function EmptyRAG({ onUpload }: EmptyRAGProps) {
  return (
    <EmptyState
      icon={<MessageSquareText className="h-12 w-12" />}
      title="لم يتم استيراد مستندات بعد"
      description="ارفع ملفات تعريف الشركات (PDF, DOCX, TXT) لبناء قاعدة معرفتك. بعدها يمكنك طرح أسئلة عن أي شركة."
      action={onUpload ? { label: "رفع مستندات", onClick: onUpload } : undefined}
      tourId="rag"
    />
  )
}
