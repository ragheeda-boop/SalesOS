"use client"

import { Video } from "lucide-react"
import { EmptyState } from "./EmptyState"

interface EmptyMeetingsProps {
  onConnectCalendar?: () => void
  onAddMeeting?: () => void
}

export function EmptyMeetings({ onConnectCalendar, onAddMeeting }: EmptyMeetingsProps) {
  return (
    <EmptyState
      icon={<Video className="h-12 w-12" />}
      title="لا توجد اجتماعات مسجلة"
      description="قم بتوصيل التقويم الخاص بك لعرض الاجتماعات تلقائياً، أو أضف اجتماعاً يدوياً."
      action={onConnectCalendar ? { label: "توصيل التقويم", onClick: onConnectCalendar } : undefined}
      secondaryAction={onAddMeeting ? { label: "إضافة اجتماع", onClick: onAddMeeting } : undefined}
    />
  )
}
