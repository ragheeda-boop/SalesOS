"use client";

import { useEntityActivity } from "@/lib/hooks/activityQueries";
import { Card, CardContent, CardHeader, cn } from "@salesos/ui";
import { Mail, Phone, Calendar, CheckSquare, FileText, MessageSquare, Edit3, Plus, Clock, User } from "lucide-react";

const actionConfig: Record<string, { icon: typeof Mail; color: string }> = {
  email_sent: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  email_received: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  meeting_created: { icon: Calendar, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  meeting_completed: { icon: Calendar, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  call: { icon: Phone, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  task_created: { icon: CheckSquare, color: "text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/50" },
  task_completed: { icon: CheckSquare, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  contract_signed: { icon: FileText, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50" },
  contract_created: { icon: FileText, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50" },
  note_added: { icon: MessageSquare, color: "text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800" },
  note_updated: { icon: Edit3, color: "text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800" },
  company_created: { icon: Plus, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50" },
  opportunity_created: { icon: Plus, color: "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50" },
  opportunity_won: { icon: CheckSquare, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50" },
  opportunity_lost: { icon: Clock, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50" },
};

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "الآن";
  if (mins < 60) return `منذ ${mins} دقيقة`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `منذ ${hours} ساعة`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `منذ ${days} يوم`;
  return new Intl.DateTimeFormat("ar-SA", { day: "numeric", month: "short" }).format(new Date(timestamp));
}

function getActionLabel(action: string): string {
  const labels: Record<string, string> = {
    email_sent: "إرسال بريد إلكتروني",
    email_received: "استلام بريد إلكتروني",
    meeting_created: "اجتماع جديد",
    meeting_completed: "اجتماع منتهي",
    call: "مكالمة هاتفية",
    task_created: "مهمة جديدة",
    task_completed: "إنجاز مهمة",
    contract_signed: "توقيع عقد",
    contract_created: "عقد جديد",
    note_added: "إضافة ملاحظة",
    note_updated: "تحديث ملاحظة",
    company_created: "إضافة شركة",
    opportunity_created: "فرصة جديدة",
    opportunity_won: "ربح فرصة",
    opportunity_lost: "خسارة فرصة",
  };
  return labels[action] || action;
}

interface TimelineWidgetProps {
  entityType: string;
  entityId: string;
  title?: string;
  limit?: number;
  className?: string;
}

export function TimelineWidget({ entityType, entityId, title, limit = 20, className }: TimelineWidgetProps) {
  const { data, isLoading } = useEntityActivity(entityType, entityId, limit);

  const activities = data?.items || [];

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
            {title || "النشاطات"}
          </h3>
          {data && <span className="text-xs text-neutral-500">{data.total} نشاط</span>}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-neutral-200 dark:bg-neutral-700" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 w-3/4 rounded bg-neutral-200 dark:bg-neutral-700" />
                  <div className="h-2 w-1/2 rounded bg-neutral-200 dark:bg-neutral-700" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
          <p className="py-8 text-center text-sm text-neutral-500 dark:text-neutral-400">لا توجد نشاطات حتى الآن</p>
        ) : (
          <div className="space-y-0">
            {activities.map((activity, idx) => {
              const config = actionConfig[activity.action] || { icon: Clock, color: "text-neutral-600 bg-neutral-100" };
              const Icon = config.icon;
              return (
                <div key={activity.id} className="relative flex gap-3 pb-4 last:pb-0">
                  {idx < activities.length - 1 && (
                    <div className="absolute right-[15px] top-10 bottom-0 w-px bg-neutral-200 dark:bg-neutral-700" />
                  )}
                  <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", config.color)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                      {getActionLabel(activity.action)}
                    </p>
                    <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                      <span className="inline-flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {activity.actor}
                      </span>
                      <span className="mx-1.5">·</span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatRelativeTime(activity.timestamp)}
                      </span>
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
