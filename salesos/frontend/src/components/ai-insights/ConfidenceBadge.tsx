"use client";

import { cn } from "@salesos/ui";
import { useTranslation } from "@/lib/i18n";
import type { ConfidenceLevel } from "./types";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  score?: number;
  className?: string;
}

const LEVEL_STYLES: Record<ConfidenceLevel, string> = {
  high: "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400",
  medium: "bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400",
  low: "bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400",
};

const LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  high: "ai_insights.confidence_high",
  medium: "ai_insights.confidence_medium",
  low: "ai_insights.confidence_low",
};

export function ConfidenceBadge({ level, score, className }: ConfidenceBadgeProps) {
  const { t } = useTranslation();

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold",
        LEVEL_STYLES[level],
        className
      )}
      title={score !== undefined ? `${Math.round(score * 100)}%` : undefined}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          level === "high" && "bg-success-500",
          level === "medium" && "bg-warning-500",
          level === "low" && "bg-danger-500"
        )}
      />
      {t(LEVEL_LABELS[level])}
    </span>
  );
}

export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "medium";
  return "low";
}
