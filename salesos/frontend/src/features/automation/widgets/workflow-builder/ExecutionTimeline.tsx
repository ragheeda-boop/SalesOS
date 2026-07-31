"use client";

import { useState } from "react";
import { useWorkflowExecutions } from "@/lib/workflowQueries";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  running: { label: "جاري", color: "#3B82F6" },
  completed: { label: "مكتمل", color: "#10B981" },
  failed: { label: "فشل", color: "#EF4444" },
  timed_out: { label: "انتهت المهلة", color: "#F59E0B" },
};

interface StepResultEntry {
  status: string;
  step_type?: string;
  duration_ms?: number;
}

function toStepResultEntry(sr: Record<string, unknown>): StepResultEntry {
  return {
    status: typeof sr.status === "string" ? sr.status : "unknown",
    step_type: typeof sr.step_type === "string" ? sr.step_type : undefined,
    duration_ms:
      typeof sr.duration_ms === "number" ? sr.duration_ms : undefined,
  };
}

interface ExecutionTimelineProps {
  workflowId: string;
}

export function ExecutionTimeline({ workflowId }: ExecutionTimelineProps) {
  const {
    data: executions,
    isLoading,
    error,
  } = useWorkflowExecutions(workflowId);
  const [expanded, setExpanded] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2 p-2">
        <div className="h-6 w-32 bg-[var(--bg-tertiary)] rounded" />
        <div className="h-10 bg-[var(--bg-secondary)] rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-xs text-danger-500 p-2">فشل تحميل سجل التنفيذ</div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="text-xs text-[var(--text-muted)] p-4 text-center">
        لا يوجد سجل تنفيذ بعد
      </div>
    );
  }

  return (
    <div className="space-y-2" dir="rtl">
      <h4 className="text-xs font-semibold text-[var(--text-muted)] px-1">
        سجل التنفيذ
      </h4>

      {executions.map((exec) => {
        const status = STATUS_LABELS[exec.status] || {
          label: exec.status,
          color: "#9CA3AF",
        };
        const isExpanded = expanded === exec.id;

        return (
          <div
            key={exec.id}
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)]"
          >
            <button
              onClick={() => setExpanded(isExpanded ? null : exec.id)}
              className="w-full flex items-center justify-between p-3 text-left"
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: status.color }}
                />
                <span className="text-xs font-medium text-[var(--text-primary)]">
                  تشغيل {new Date(exec.started_at).toLocaleDateString("ar-SA")}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[var(--text-muted)]">
                  {exec.step_results?.length || 0} خطوة
                </span>
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    backgroundColor: status.color + "20",
                    color: status.color,
                  }}
                >
                  {status.label}
                </span>
                {exec.completed_at != null && (
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {Math.round(
                      (new Date(exec.completed_at).getTime() -
                        new Date(exec.started_at).getTime()) /
                        1000,
                    )}
                    ث
                  </span>
                )}
              </div>
            </button>

            {isExpanded &&
              exec.step_results &&
              exec.step_results.length > 0 && (
                <div className="border-t border-[var(--border-default)] px-3 pb-3 pt-2">
                  <div className="space-y-1">
                    {exec.step_results.map((raw, i) => {
                      const sr = toStepResultEntry(raw);
                      const s = STATUS_LABELS[sr.status] || {
                        label: sr.status,
                        color: "#9CA3AF",
                      };
                      return (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-[10px]"
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full shrink-0"
                            style={{ backgroundColor: s.color }}
                          />
                          <span className="text-[var(--text-secondary)] w-6 tabular-nums">
                            {i + 1}
                          </span>
                          <span className="text-[var(--text-primary)]">
                            {sr.step_type || "—"}
                          </span>
                          <span className="text-[var(--text-muted)] ml-auto">
                            {s.label}
                          </span>
                          {sr.duration_ms != null && (
                            <span className="text-[var(--text-muted)] tabular-nums">
                              {sr.duration_ms}ms
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

            {isExpanded &&
              (!exec.step_results || exec.step_results.length === 0) && (
                <div className="border-t border-[var(--border-default)] px-3 pb-3 pt-2">
                  <span className="text-[10px] text-[var(--text-muted)]">
                    لا توجد تفاصيل للخطوات
                  </span>
                </div>
              )}
          </div>
        );
      })}
    </div>
  );
}
