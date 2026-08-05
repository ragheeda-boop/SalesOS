"use client";

import { cn } from "@salesos/ui";
import {
  CalendarClock,
  RotateCcw,
  ClipboardCheck,
  AlertTriangle,
  Clock,
  CircleCheckBig,
} from "lucide-react";
import type { MorningBriefData, MorningBriefItem } from "./types";

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-danger-100 text-danger-800 dark:bg-danger-900/30 dark:text-danger-300",
  medium: "bg-warning-100 text-warning-800 dark:bg-warning-900/30 dark:text-warning-300",
  low: "bg-info-100 text-info-800 dark:bg-info-900/30 dark:text-info-300",
};

const TYPE_ICON: Record<string, React.ReactNode> = {
  meeting: <CalendarClock className="h-4 w-4" />,
  "follow-up": <RotateCcw className="h-4 w-4" />,
  task: <ClipboardCheck className="h-4 w-4" />,
  deal: <AlertTriangle className="h-4 w-4" />,
  signal: <Clock className="h-4 w-4" />,
};

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
        PRIORITY_BADGE[priority] ?? PRIORITY_BADGE.low,
      )}
    >
      {priority === "high" ? "عالي" : priority === "medium" ? "متوسط" : "منخفض"}
    </span>
  );
}

function BriefItemRow({ item }: { item: MorningBriefItem }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors",
        item.completed
          ? "bg-[var(--bg-tertiary)] opacity-60"
          : "bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)]",
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          item.type === "deal"
            ? "bg-danger-100 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400"
            : item.type === "meeting"
              ? "bg-info-100 text-info-600 dark:bg-info-900/30 dark:text-info-400"
              : "bg-[var(--bg-tertiary)] text-[var(--text-muted)]",
        )}
      >
        {item.completed ? (
          <CircleCheckBig className="h-4 w-4 text-success-600" />
        ) : (
          TYPE_ICON[item.type]
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "text-sm font-medium",
            item.completed
              ? "text-[var(--text-muted)] line-through"
              : "text-[var(--text-primary)]",
          )}
        >
          {item.title}
        </p>
        {item.companyName && (
          <p className="text-xs text-[var(--text-muted)]">{item.companyName}</p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {item.time && (
          <span className="text-xs text-[var(--text-muted)]">{item.time}</span>
        )}
        <PriorityBadge priority={item.priority} />
      </div>
    </div>
  );
}

function StatPill({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-[var(--bg-secondary)] px-3 py-2">
      <div className={cn("flex h-7 w-7 items-center justify-center rounded-md", color)}>
        {icon}
      </div>
      <div>
        <p className="text-lg font-bold text-[var(--text-primary)] tabular-nums">
          {value}
        </p>
        <p className="text-[10px] text-[var(--text-muted)]">{label}</p>
      </div>
    </div>
  );
}

export function MorningBriefView({ data }: { data: MorningBriefData }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-[var(--text-primary)]">
            {data.greeting}
          </h2>
          <p className="text-xs text-[var(--text-muted)]">{data.date}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatPill
            icon={<CalendarClock className="h-3.5 w-3.5 text-info-600" />}
            label="اجتماعات"
            value={data.stats.meetingsToday}
            color="bg-info-50 dark:bg-info-950/30"
          />
          <StatPill
            icon={<RotateCcw className="h-3.5 w-3.5 text-warning-600" />}
            label="متابعات"
            value={data.stats.pendingFollowUps}
            color="bg-warning-50 dark:bg-warning-950/30"
          />
          <StatPill
            icon={<ClipboardCheck className="h-3.5 w-3.5 text-[var(--muhide-orange)]" />}
            label="مهام"
            value={data.stats.openTasks}
            color="bg-orange-50 dark:bg-orange-950/30"
          />
          <StatPill
            icon={<AlertTriangle className="h-3.5 w-3.5 text-danger-600" />}
            label="صفقات معرضة للخطر"
            value={data.stats.atRiskDeals}
            color="bg-danger-50 dark:bg-danger-950/30"
          />
        </div>
      </div>

      {data.priorities.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-[var(--text-muted)]">
            أولويات اليوم
          </p>
          <div className="space-y-1.5">
            {data.priorities.map((item) => (
              <BriefItemRow key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
