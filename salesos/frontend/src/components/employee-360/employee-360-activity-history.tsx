"use client";

import { Card, CardContent, CardHeader, EmptyState, Badge, cn } from "@salesos/ui";
import { Clock } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { formatRelativeTime, getActionConfig } from "./employee-360-shared";

interface ActivityEvent {
  id: string;
  action: string;
  title: string;
  source_label: string;
  timestamp: string;
  actor?: string;
}

interface ActivityHistoryProps {
  events: ActivityEvent[];
  isLoading?: boolean;
  maxItems?: number;
}

export function ActivityHistory({ events, isLoading, maxItems = 10 }: ActivityHistoryProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold">{t("emp360.activity_history")}</h3>
        </CardHeader>
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
    );
  }

  if (events.length === 0) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold">{t("emp360.activity_history")}</h3>
        </CardHeader>
        <CardContent>
          <EmptyState icon={<Clock className="h-8 w-8" />} title={t("emp360.no_activity")} />
        </CardContent>
      </Card>
    );
  }

  const displayEvents = events.slice(0, maxItems);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">{t("emp360.activity_history")}</h3>
          <Badge variant="default" className="text-[10px]">
            {events.length} {t("emp360.events")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-0">
          {displayEvents.map((event, idx) => {
            const config = getActionConfig(event.action);
            const Icon = config.icon;
            return (
              <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                {idx < displayEvents.length - 1 && (
                  <div className="absolute right-[15px] top-10 bottom-0 w-px bg-[var(--bg-tertiary)]" />
                )}
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    config.color
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{event.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                    <Badge variant="default" className="me-1 text-[10px]">
                      {event.source_label}
                    </Badge>
                    {event.actor && <span className="me-1">· {event.actor}</span>}
                    <span>· {formatRelativeTime(event.timestamp)}</span>
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
