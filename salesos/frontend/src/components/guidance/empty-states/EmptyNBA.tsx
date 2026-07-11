"use client"

import { Lightbulb } from "lucide-react"
import { EmptyState } from "./EmptyState"

interface EmptyNBAProps {
  onCreateOpportunity?: () => void
}

export function EmptyNBA({ onCreateOpportunity }: EmptyNBAProps) {
  return (
    <EmptyState
      icon={<Lightbulb className="h-12 w-12" />}
      title="التوصيات بحاجة لبيانات"
      description="نظام التوصيات الذكية يحتاج إلى بيانات صفقات في خط الأنابيب. أضف فرصاً جديدة لبدء تلقي التوصيات."
      action={onCreateOpportunity ? { label: "إضافة فرصة", onClick: onCreateOpportunity } : undefined}
      tourId="nba"
    />
  )
}
