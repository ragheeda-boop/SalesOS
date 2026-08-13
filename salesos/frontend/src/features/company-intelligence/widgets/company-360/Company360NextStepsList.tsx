"use client";

import { Target } from "lucide-react";
import { EmptyState, cn } from "@salesos/ui";
import { asTaskRows } from "./company360Lists";

function priorityClass(priority: string): string {
  if (priority === "عاجل" || priority === "high" || priority === "urgent") {
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  }
  if (priority === "منخفض" || priority === "low") {
    return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
  }
  return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
}

export function Company360NextStepsList({ tasks }: { tasks: unknown }) {
  const rows = asTaskRows(tasks);
  if (rows.length === 0) {
    return (
      <EmptyState
        icon={<Target className="h-10 w-10" />}
        title="لا توجد خطوات تالية"
        description="لم يتم تحديد خطوات تالية لهذه الشركة"
      />
    );
  }
  return (
    <div className="space-y-3">
      {rows.map((step) => (
        <div
          key={step.id}
          className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-default)]"
        >
          <div className="flex items-center gap-3 min-w-0">
            <input
              type="checkbox"
              readOnly
              checked={step.status === "completed"}
              className="rounded border-[var(--border-default)]"
              aria-label={step.text}
            />
            <div className="min-w-0">
              <div className="font-medium text-[var(--text-primary)] truncate">{step.text}</div>
              {step.dueDate ? (
                <div className="text-xs text-[var(--text-muted)]">{step.dueDate}</div>
              ) : null}
            </div>
          </div>
          <span
            className={cn(
              "px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0 ml-3",
              priorityClass(step.priority)
            )}
          >
            {step.priority}
          </span>
        </div>
      ))}
    </div>
  );
}
