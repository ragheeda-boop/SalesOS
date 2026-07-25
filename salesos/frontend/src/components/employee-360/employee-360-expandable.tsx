"use client"

import { useEmployeeTimeline } from "@/lib/hooks/employeeQueries"
import { Card, CardContent, CardHeader, Skeleton, EmptyState, Badge, cn } from "@salesos/ui"
import { Clock } from "lucide-react"
import { useTranslation } from "@/lib/i18n"
import { formatRelativeTime, getActionConfig } from "./employee-360-shared"

export function OverviewSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
      </div>
      <Skeleton className="h-48" />
    </div>
  )
}

export function RecentActivityFeed({ employeeId }: { employeeId: string }) {
  const { t } = useTranslation()
  const { data, isLoading } = useEmployeeTimeline(employeeId, { page_size: 5 })

  if (isLoading) {
    return (
      <Card>
        <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-[var(--bg-tertiary)]" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 w-3/4 rounded bg-[var(--bg-tertiary)]" />
                  <div className="h-2 w-1/2 rounded bg-[var(--bg-tertiary)]" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const events = data?.events || []

  if (events.length === 0) {
    return (
      <Card>
        <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
        <CardContent>
          <EmptyState icon={<Clock className="h-8 w-8" />} title={t("emp360.no_activity")} />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader><h3 className="text-sm font-semibold">{t("emp360.recent_activity")}</h3></CardHeader>
      <CardContent>
        <div className="space-y-0">
          {events.map((event, idx) => {
            const config = getActionConfig(event.action)
            const Icon = config.icon
            return (
              <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                {idx < events.length - 1 && (
                  <div className="absolute right-[15px] top-10 bottom-0 w-px bg-[var(--bg-tertiary)]" />
                )}
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", config.color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{event.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                    <span className="inline-flex items-center gap-1">
                      <Badge variant="default" className="text-[10px]">{event.source_label}</Badge>
                    </span>
                    <span className="mx-1.5">·</span>
                    {formatRelativeTime(event.timestamp)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
