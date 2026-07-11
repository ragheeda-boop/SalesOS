"use client"

import { Workflow } from "lucide-react"
import { EmptyState } from "./EmptyState"

interface EmptyWorkflowsProps {
  onCreateWorkflow?: () => void
  onBrowseTemplates?: () => void
}

export function EmptyWorkflows({ onCreateWorkflow, onBrowseTemplates }: EmptyWorkflowsProps) {
  return (
    <EmptyState
      icon={<Workflow className="h-12 w-12" />}
      title="لا توجد أتمتة بعد"
      description="أنشئ أول سير عمل لأتمتة مهامك المتكررة، أو ابدأ بقالب جاهز لتوفير الوقت."
      action={onCreateWorkflow ? { label: "إنشاء سير عمل", onClick: onCreateWorkflow } : undefined}
      secondaryAction={onBrowseTemplates ? { label: "تصفح القوالب", onClick: onBrowseTemplates } : undefined}
      tourId="workflow"
    />
  )
}
