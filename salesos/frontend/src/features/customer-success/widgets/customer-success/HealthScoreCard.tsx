"use client";

import { cn } from "@salesos/ui";
import { HeartPulse, TrendingUp, TrendingDown } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface HealthScoreCardProps {
  score: number;
  label: string;
  thresholds: { green: number; yellow: number };
}

export function HealthScoreCard({
  score,
  label,
  thresholds,
}: HealthScoreCardProps) {
  const { t } = useTranslation();

  const color =
    score >= thresholds.green
      ? "text-[var(--status-success-text)]"
      : score >= thresholds.yellow
        ? "text-yellow-600"
        : "text-[var(--status-danger-text)]";

  const bgColor =
    score >= thresholds.green
      ? "bg-[var(--status-success-bg)] border-[var(--status-success-border)]"
      : score >= thresholds.yellow
        ? "bg-yellow-50 border-yellow-200"
        : "bg-[var(--status-danger-bg)] border-[var(--status-danger-border)]";

  return (
    <div className={cn("rounded-xl border p-4", bgColor)}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-[var(--text-muted)]">{label}</p>
        <HeartPulse className={cn("h-5 w-5", color)} />
      </div>
      <p className={cn("text-2xl font-display font-bold", color)}>
        {score.toFixed(0)}%
      </p>
      <div className="flex items-center gap-1 mt-1">
        {score >= thresholds.green ? (
          <TrendingUp className="h-3 w-3 text-[var(--status-success-text)]" />
        ) : (
          <TrendingDown className="h-3 w-3 text-[var(--status-danger-text)]" />
        )}
        <span className="text-xs text-[var(--text-muted)]">
          {score >= thresholds.green
            ? t("cs.good")
            : score >= thresholds.yellow
              ? t("cs.needs_improvement")
              : t("cs.critical")}
        </span>
      </div>
    </div>
  );
}
