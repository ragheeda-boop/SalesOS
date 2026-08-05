"use client";

import type { ElementType, ReactNode } from "react";
import { cn } from "@salesos/ui";
import { Mail, Calendar, CheckCircle, Phone, Clock } from "lucide-react";

export function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined)
    return <span className="text-[var(--text-disabled)]">-</span>;
  const color =
    score >= 70
      ? "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400"
      : score >= 40
        ? "bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400"
        : "bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400";
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${color}`}
    >
      {score}
    </span>
  );
}

export function StatBox({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: ElementType;
  label: string;
  value: ReactNode;
  color: string;
}) {
  return (
    <div className={cn("flex items-center gap-3 rounded-xl p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-[10px] opacity-70">{label}</p>
        <p className="text-lg font-bold">{value}</p>
      </div>
    </div>
  );
}

export const actionConfig: Record<string, { icon: typeof Mail; color: string }> = {
  email_sent: {
    icon: Mail,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
  },
  email_received: {
    icon: Mail,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
  },
  meeting_created: {
    icon: Calendar,
    color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50",
  },
  meeting_completed: {
    icon: Calendar,
    color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
  },
  call: {
    icon: Phone,
    color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
  },
  task_created: {
    icon: CheckCircle,
    color: "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50",
  },
  task_completed: {
    icon: CheckCircle,
    color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50",
  },
  note_added: {
    icon: Mail,
    color: "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
  },
  contract_signed: {
    icon: CheckCircle,
    color:
      "text-[var(--chart-purple)] bg-[var(--chart-purple-bg)] dark:text-[var(--chart-purple)] dark:bg-[var(--bg-primary)]/50",
  },
};

export function getActionConfig(action: string) {
  return (
    actionConfig[action] || {
      icon: Clock,
      color: "text-[var(--text-secondary)] bg-[var(--bg-tertiary)]",
    }
  );
}

export const SOURCE_OPTIONS = ["crm", "timeline", "workflow", "email", "calendar", "manual"];
export const TYPE_OPTIONS = [
  "email_sent",
  "email_received",
  "meeting_created",
  "meeting_completed",
  "call",
  "task_created",
  "task_completed",
  "note_added",
  "contract_signed",
];
