"use client";

import { useState, useMemo } from "react";
import { useGlobalActivities } from "@/lib/hooks/activityQueries";
import { Card, CardContent, Badge, Button, Spinner, Input } from "@salesos/ui";
import {
  Activity,
  Mail,
  Phone,
  Calendar,
  CheckSquare,
  FileText,
  MessageSquare,
  Edit3,
  Plus,
  Clock,
  User,
  Search,
  AlertTriangle,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";

const ACTION_CONFIG: Record<
  string,
  { icon: typeof Mail; color: string; labelKey: string }
> = {
  email_sent: {
    icon: Mail,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
    labelKey: "activity.email_sent",
  },
  email_received: {
    icon: Mail,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
    labelKey: "activity.email_received",
  },
  meeting_created: {
    icon: Calendar,
    color:
      "text-[var(--chart-purple)] bg-[var(--chart-purple-bg)] dark:text-[var(--chart-purple)] dark:bg-[var(--bg-primary)]/50",
    labelKey: "activity.meeting_created",
  },
  meeting_completed: {
    icon: Calendar,
    color:
      "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
    labelKey: "activity.meeting_completed",
  },
  call: {
    icon: Phone,
    color:
      "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
    labelKey: "activity.call",
  },
  task_created: {
    icon: CheckSquare,
    color:
      "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50",
    labelKey: "activity.task_created",
  },
  task_completed: {
    icon: CheckSquare,
    color:
      "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
    labelKey: "activity.task_completed",
  },
  contract_signed: {
    icon: FileText,
    color:
      "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50",
    labelKey: "activity.contract_signed",
  },
  contract_created: {
    icon: FileText,
    color:
      "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50",
    labelKey: "activity.contract_created",
  },
  note_added: {
    icon: MessageSquare,
    color: "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
    labelKey: "activity.note",
  },
  note_updated: {
    icon: Edit3,
    color: "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
    labelKey: "activity.note_updated",
  },
  company_created: {
    icon: Plus,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
    labelKey: "activity.company_created",
  },
  opportunity_created: {
    icon: Plus,
    color:
      "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50",
    labelKey: "activity.opportunity_created",
  },
  opportunity_won: {
    icon: CheckSquare,
    color:
      "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
    labelKey: "activity.opportunity_won",
  },
  opportunity_lost: {
    icon: Clock,
    color:
      "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50",
    labelKey: "activity.opportunity_lost",
  },
};

function formatRelativeTime(
  timestamp: string,
  t: (key: string, params?: Record<string, string | number>) => string,
): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return t("time.just_now");
  if (mins < 60) return t("time.minutes_ago", { count: mins });
  const hours = Math.floor(mins / 60);
  if (hours < 24) return t("time.hours_ago", { count: hours });
  const days = Math.floor(hours / 24);
  if (days < 30) return t("time.days_ago", { count: days });
  return new Intl.DateTimeFormat("ar-SA", {
    day: "numeric",
    month: "short",
  }).format(new Date(timestamp));
}

function groupByDate<T extends { timestamp: string }>(items: T[]) {
  const groups: Record<string, T[]> = {};
  for (const item of items) {
    const date = new Date(item.timestamp).toLocaleDateString("ar-SA", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    if (!groups[date]) groups[date] = [];
    groups[date].push(item);
  }
  return groups;
}

export default function ActivitiesPage() {
  const [actionFilter, setActionFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const { t } = useTranslation();

  const ACTION_FILTERS = [
    { label: t("status.all"), value: "" },
    { label: t("activity.filter.email"), value: "email" },
    { label: t("activity.filter.meetings"), value: "meeting" },
    { label: t("activity.filter.calls"), value: "call" },
    { label: t("activity.filter.tasks"), value: "task" },
    { label: t("activity.filter.contracts"), value: "contract" },
    { label: t("activity.filter.notes"), value: "note" },
    { label: t("activity.filter.opportunities"), value: "opportunity" },
  ];

  const filters = useMemo(() => {
    const f: Record<string, string> = {};
    if (actionFilter) f.action = actionFilter;
    return f;
  }, [actionFilter]);

  const { data, isLoading, isError, error, refetch } =
    useGlobalActivities(filters);
  const activities = data?.items || [];
  const total = data?.total || 0;

  const filteredActivities = useMemo(() => {
    if (!searchQuery) return activities;
    const q = searchQuery.toLowerCase();
    return activities.filter(
      (a) =>
        a.actor.toLowerCase().includes(q) ||
        a.action.toLowerCase().includes(q) ||
        a.entity_type.toLowerCase().includes(q),
    );
  }, [activities, searchQuery]);

  const grouped = useMemo(
    () => groupByDate(filteredActivities),
    [filteredActivities],
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            {t("nav.activities")}
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {t("activities.subtitle")}
          </p>
        </div>
        {total > 0 && (
          <Badge variant="primary">
            {total} {t("activities.count_unit")}
          </Badge>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder={t("activities.search_placeholder")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
          className="max-w-xs"
        />
        <div className="flex gap-1 overflow-x-auto rounded-lg border border-[var(--border-default)] px-1 py-0.5">
          {ACTION_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setActionFilter(f.value)}
              className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs transition ${
                actionFilter === f.value
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Activity Feed */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Spinner className="h-6 w-6" />
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <AlertTriangle className="mb-3 h-10 w-10 text-danger-500" />
              <p className="text-lg font-semibold text-[var(--text-primary)]">
                {t("activities.load_error")}
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                {(error as Error)?.message || t("activities.check_server")}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-4"
                onClick={() => refetch()}
              >
                {t("common.retry")}
              </Button>
            </div>
          ) : filteredActivities.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Activity className="mb-3 h-10 w-10 text-[var(--text-disabled)]" />
              <p className="text-lg font-semibold text-[var(--text-primary)]">
                {searchQuery || actionFilter
                  ? t("common.no_results")
                  : t("activities.empty")}
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                {searchQuery || actionFilter
                  ? t("activities.try_different_search")
                  : t("activities.empty_hint")}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {Object.entries(grouped).map(([date, items]) => (
                <div key={date}>
                  <div className="sticky top-0 z-10 bg-[var(--bg-secondary)] px-4 py-2 text-xs font-medium text-[var(--text-muted)]">
                    {date}
                  </div>
                  <div className="divide-y divide-neutral-50 dark:divide-neutral-800/50">
                    {items.map((activity) => {
                      const config = ACTION_CONFIG[activity.action] || {
                        icon: Clock,
                        color:
                          "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
                        labelKey: "",
                      };
                      const Icon = config.icon;
                      return (
                        <div
                          key={activity.id}
                          className="flex items-start gap-3 px-4 py-3 transition hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/30"
                        >
                          <div
                            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${config.color}`}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-[var(--text-primary)]">
                                {config.labelKey
                                  ? t(config.labelKey)
                                  : activity.action}
                              </span>
                              <Badge variant="default" className="text-[9px]">
                                {activity.entity_type}
                              </Badge>
                            </div>
                            <div className="mt-0.5 flex items-center gap-2 text-xs text-[var(--text-muted)]">
                              <span className="inline-flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {activity.actor}
                              </span>
                              <span>·</span>
                              <span className="inline-flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatRelativeTime(activity.timestamp, t)}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
