"use client";

import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useEntityActivity } from "@/lib/hooks/activityQueries";
import {
  Card,
  CardContent,
  CardHeader,
  cn,
  Skeleton,
  EmptyState,
} from "@salesos/ui";
import {
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
  Filter,
  X,
} from "lucide-react";

interface ActivityTimelineProps {
  companyId: string;
  limit?: number;
}

const ACTION_CONFIG: Record<
  string,
  { icon: typeof Mail; color: string; label: string; category: string }
> = {
  email_sent: {
    icon: Mail,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    label: "إرسال بريد إلكتروني",
    category: "email",
  },
  email_received: {
    icon: Mail,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    label: "استلام بريد إلكتروني",
    category: "email",
  },
  meeting_created: {
    icon: Calendar,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    label: "اجتماع جديد",
    category: "meeting",
  },
  meeting_completed: {
    icon: Calendar,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    label: "اجتماع منتهي",
    category: "meeting",
  },
  call: {
    icon: Phone,
    color: "text-[var(--color-success)] bg-[var(--color-success-bg)]",
    label: "مكالمة هاتفية",
    category: "call",
  },
  task_created: {
    icon: CheckSquare,
    color: "text-[var(--color-warning)] bg-[var(--color-warning-bg)]",
    label: "مهمة جديدة",
    category: "task",
  },
  task_completed: {
    icon: CheckSquare,
    color: "text-[var(--color-success)] bg-[var(--color-success-bg)]",
    label: "إنجاز مهمة",
    category: "task",
  },
  contract_signed: {
    icon: FileText,
    color: "text-[var(--color-danger)] bg-[var(--color-danger-bg)]",
    label: "توقيع عقد",
    category: "contract",
  },
  contract_created: {
    icon: FileText,
    color: "text-[var(--color-danger)] bg-[var(--color-danger-bg)]",
    label: "عقد جديد",
    category: "contract",
  },
  note_added: {
    icon: MessageSquare,
    color: "text-[var(--color-neutral)] bg-[var(--color-neutral-bg)]",
    label: "إضافة ملاحظة",
    category: "note",
  },
  note_updated: {
    icon: Edit3,
    color: "text-[var(--color-neutral)] bg-[var(--color-neutral-bg)]",
    label: "تحديث ملاحظة",
    category: "note",
  },
  company_created: {
    icon: Plus,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    label: "إضافة شركة",
    category: "other",
  },
  opportunity_created: {
    icon: Plus,
    color: "text-[var(--color-warning)] bg-[var(--color-warning-bg)]",
    label: "فرصة جديدة",
    category: "opportunity",
  },
  opportunity_won: {
    icon: CheckSquare,
    color: "text-[var(--color-success)] bg-[var(--color-success-bg)]",
    label: "ربح فرصة",
    category: "opportunity",
  },
  opportunity_lost: {
    icon: Clock,
    color: "text-[var(--color-danger)] bg-[var(--color-danger-bg)]",
    label: "خسارة فرصة",
    category: "opportunity",
  },
};

const FILTER_CHIPS = [
  {
    key: "email",
    label: "بريد",
    color: "bg-[var(--color-info-bg)] text-[var(--color-info)]",
  },
  {
    key: "meeting",
    label: "اجتماعات",
    color: "bg-[var(--color-info-bg)] text-[var(--color-info)]",
  },
  {
    key: "call",
    label: "مكالمات",
    color: "bg-[var(--color-success-bg)] text-[var(--color-success)]",
  },
  {
    key: "task",
    label: "مهام",
    color: "bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
  },
  {
    key: "contract",
    label: "عقود",
    color: "bg-[var(--color-danger-bg)] text-[var(--color-danger)]",
  },
  {
    key: "note",
    label: "ملاحظات",
    color: "bg-[var(--color-neutral-bg)] text-[var(--color-neutral)]",
  },
  {
    key: "opportunity",
    label: "فرص",
    color: "bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
  },
];

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "الآن";
  if (mins < 60) return `منذ ${mins} دقيقة`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `منذ ${hours} ساعة`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `منذ ${days} يوم`;
  return new Intl.DateTimeFormat("ar-SA", {
    day: "numeric",
    month: "short",
  }).format(new Date(timestamp));
}

function formatDateGroup(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return "اليوم";
  if (date.toDateString() === yesterday.toDateString()) return "أمس";
  return new Intl.DateTimeFormat("ar-SA", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function ActivityTimeline({
  companyId,
  limit = 50,
}: ActivityTimelineProps) {
  const { data, isLoading, isError } = useEntityActivity(
    "company",
    companyId,
    limit,
  );
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [visibleCount, setVisibleCount] = useState(20);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const activities = data?.items || [];

  const toggleFilter = useCallback((key: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
    setVisibleCount(20);
  }, []);

  const filtered = useMemo(() => {
    if (activeFilters.size === 0) return activities;
    return activities.filter((a) => {
      const config = ACTION_CONFIG[a.action];
      return config && activeFilters.has(config.category);
    });
  }, [activities, activeFilters]);

  const groupedByDate = useMemo(() => {
    const groups: Record<string, typeof filtered> = {};
    const sliced = filtered.slice(0, visibleCount);
    for (const item of sliced) {
      const key = new Date(item.timestamp).toDateString();
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return groups;
  }, [filtered, visibleCount]);

  useEffect(() => {
    if (!sentinelRef.current || filtered.length <= visibleCount) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => Math.min(prev + 20, filtered.length));
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [filtered.length, visibleCount]);

  const hasMore = visibleCount < filtered.length;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-[var(--text-muted)]" />
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                النشاطات
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton variant="circle" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-2 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              النشاطات
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<Clock className="h-10 w-10" />}
            title="فشل تحميل النشاطات"
            description="تعذر تحميل سجل النشاطات"
          />
        </CardContent>
      </Card>
    );
  }

  if (activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              النشاطات
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<Clock className="h-10 w-10" />}
            title="لا توجد نشاطات"
            description="لم يتم تسجيل أي نشاط لهذه الشركة"
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-[var(--text-muted)]" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              النشاطات
            </span>
          </div>
          <span className="text-xs text-[var(--text-muted)]">
            {filtered.length} نشاط
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap gap-1.5">
          {FILTER_CHIPS.map((chip) => (
            <button
              key={chip.key}
              onClick={() => toggleFilter(chip.key)}
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors",
                activeFilters.has(chip.key)
                  ? "bg-[var(--bg-primary)] text-white"
                  : chip.color,
              )}
            >
              {chip.label}
              {activeFilters.has(chip.key) && <X className="h-3 w-3" />}
            </button>
          ))}
          {activeFilters.size > 0 && (
            <button
              onClick={() => {
                setActiveFilters(new Set());
                setVisibleCount(20);
              }}
              className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
            >
              <Filter className="h-3 w-3" />
              مسح
            </button>
          )}
        </div>

        {filtered.length === 0 ? (
          <EmptyState
            icon={<Clock className="h-10 w-10" />}
            title="لا توجد نتائج"
            description="جرب تغيير معايير التصفية"
          />
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedByDate).map(([dateKey, items]) => (
              <div key={dateKey}>
                <h4 className="mb-3 text-xs font-semibold text-[var(--text-muted)]">
                  {formatDateGroup(items[0].timestamp)}
                </h4>
                <div className="space-y-0">
                  {items.map((activity, idx) => {
                    const config = ACTION_CONFIG[activity.action] || {
                      icon: Clock,
                      color:
                        "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
                      label: activity.action,
                      category: "other",
                    };
                    const Icon = config.icon;
                    return (
                      <div
                        key={activity.id}
                        className="relative flex gap-3 pb-4 last:pb-0"
                      >
                        {idx < items.length - 1 && (
                          <div className="absolute right-[15px] top-10 bottom-0 w-px bg-[var(--bg-tertiary)]" />
                        )}
                        <div
                          className={cn(
                            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                            config.color,
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-[var(--text-primary)]">
                            {config.label}
                          </p>
                          <p className="mt-0.5 text-xs text-[var(--text-muted)]">
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
              </div>
            ))}
            {hasMore && <div ref={sentinelRef} className="h-4" />}
            {hasMore && (
              <p className="text-center text-xs text-[var(--text-disabled)]">
                قم بالتمرير لتحميل المزيد...
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
