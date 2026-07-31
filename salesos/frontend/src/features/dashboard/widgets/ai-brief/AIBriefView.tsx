"use client";

import { cn, EmptyState } from "@salesos/ui";
import type { AIBriefViewProps } from "./types";

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("ar-SA", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function AIBriefView({
  summary,
  highlights,
  generatedAt,
  onRefresh: _onRefresh,
}: AIBriefViewProps) {
  if (!summary || summary.trim().length === 0) {
    return (
      <div role="region" aria-label="الملخص اليومي">
        <EmptyState
          icon={<span className="text-2xl">🤖</span>}
          title="الملخص قيد الإعداد"
          description="سيظهر الملخص اليومي هنا بعد اكتماله"
        />
      </div>
    );
  }

  return (
    <div
      role="region"
      aria-label="الملخص اليومي"
      className="space-y-3/20 dark:rounded-lg dark:p-1"
    >
      <p className="text-sm leading-relaxed text-[var(--text-primary)]">
        {summary}
      </p>

      {highlights.length > 0 && (
        <div>
          <span className="text-xs font-medium text-[var(--text-muted)]">
            أبرز النقاط
          </span>
          <ul role="list" className="mt-1.5 space-y-1.5">
            {highlights.map((h, i) => (
              <li
                key={i}
                role="listitem"
                className={cn(
                  "rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none",
                  "text-[var(--text-primary)] bg-[var(--bg-tertiary)]",
                )}
              >
                {h}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="sr-only" aria-live="polite">
        آخر تحديث: {formatDateTime(generatedAt)}
      </p>
    </div>
  );
}
