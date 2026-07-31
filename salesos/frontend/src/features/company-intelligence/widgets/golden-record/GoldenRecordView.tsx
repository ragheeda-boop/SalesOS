"use client";

import { cn } from "@salesos/ui";
import { Database, AlertTriangle, CheckCircle } from "lucide-react";
import type { GoldenRecordViewProps } from "./types";

const STATUS_V = {
  matched: "text-[var(--status-success-text)]",
  potential_duplicate: "text-[var(--status-warning-text)]",
  conflict: "text-[var(--status-danger-text)]",
};
const STATUS_L = {
  matched: "متطابق",
  potential_duplicate: "تكرار محتمل",
  conflict: "تعارض",
};

export function GoldenRecordView({ entries, dna }: GoldenRecordViewProps) {
  const hasContent = entries.length > 0 || dna;

  if (!hasContent) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Database className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">
          لا توجد بيانات السجل الذهبي
        </p>
      </div>
    );
  }

  return (
    <div
      role="region"
      aria-label="السجل الذهبي"
      className="space-y-1/20 dark:rounded-lg dark:p-1"
    >
      {dna && (
        <div className="flex items-center gap-2 rounded-lg bg-[var(--status-success-bg)]/50 px-3 py-2">
          <CheckCircle className="h-4 w-4 shrink-0 text-[var(--status-success-text)]" />
          <div>
            <p className="text-[10px] font-medium text-[var(--status-success-text)]">
              {dna.goldenRecordStatus.status === "clean"
                ? "سجل ذهبي نظيف"
                : dna.goldenRecordStatus.status === "needs_review"
                  ? "بحاجة مراجعة"
                  : "تعارض"}
            </p>
            <p className="text-[9px] text-[var(--status-success-text)]">
              {dna.goldenRecordStatus.sources} مصادر · %
              {Math.round(dna.confidenceScore * 100)} ثقة
            </p>
          </div>
        </div>
      )}

      {entries.map((entry) => (
        <div
          key={entry.id}
          className="flex items-start gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]"
        >
          {entry.status === "conflict" ? (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--status-danger-text)]" />
          ) : entry.status === "potential_duplicate" ? (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--status-warning-text)]" />
          ) : (
            <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--status-success-text)]" />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-[var(--text-primary)]">
                {entry.entityName}
              </span>
              <span
                className={cn(
                  "mr-auto text-[9px] font-medium",
                  STATUS_V[entry.status],
                )}
              >
                {STATUS_L[entry.status]}
              </span>
            </div>
            <div className="flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
              <span>{entry.source}</span>
              <span>%{Math.round(entry.confidence * 100)}</span>
              {entry.conflicts.length > 0 && (
                <span>{entry.conflicts.length} تعارض</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
