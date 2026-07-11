"use client"

import { TrendingUp } from "lucide-react"
import { EmptyState } from "./EmptyState"

interface EmptyPipelineProps {
  onCreateOpportunity?: () => void
  onImport?: () => void
}

export function EmptyPipeline({ onCreateOpportunity, onImport }: EmptyPipelineProps) {
  return (
    <EmptyState
      icon={<TrendingUp className="h-12 w-12" />}
      title="لا توجد صفقات بعد"
      description="ابدأ باستيراد بيانات فرصك الحالية أو أنشئ أول فرصة لك. ستظهر الصفقات هنا في لوحة كانبان."
      action={onCreateOpportunity ? { label: "إنشاء فرصة جديدة", onClick: onCreateOpportunity } : undefined}
      secondaryAction={onImport ? { label: "استيراد بيانات", onClick: onImport } : undefined}
      tourId="pipeline"
    />
  )
}
