"use client";

import { Sparkles, TrendingUp, AlertTriangle, Clock, DollarSign } from "lucide-react";
import type { AIRecommendationViewProps } from "./types";

export function AIRecommendationView({ recommendation }: AIRecommendationViewProps) {
  if (!recommendation) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Sparkles className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد توصيات متاحة</p>
      </div>
    );
  }

  return (
    <div role="region" aria-label="توصيات AI" className="space-y-3/20 dark:rounded-lg dark:p-1">
      <div className="rounded-lg border border-[var(--border-default)] bg-[var(--chart-purple-bg)]/50 p-3 dark:border-[var(--border-strong)] dark:bg-[var(--bg-primary)]/10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[var(--chart-purple)]" />
          <span className="text-sm font-semibold text-[var(--text-secondary)] dark:text-[var(--text-muted)]">
            {recommendation.actionLabel}
          </span>
        </div>
        <p className="mt-1.5 text-xs text-[var(--text-primary)] dark:text-[var(--text-disabled)]">
          {recommendation.reasoning}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <DollarSign className="h-3 w-3" />
            الإيرادات المتوقعة
          </div>
          <p className="mt-0.5 text-sm font-bold text-[var(--text-primary)]">
            ${(recommendation.expectedRevenue / 1000).toFixed(0)}K
          </p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <Clock className="h-3 w-3" />
            الوقت المتوقع
          </div>
          <p className="mt-0.5 text-sm font-bold text-[var(--text-primary)]">
            {recommendation.estimatedTime}
          </p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <TrendingUp className="h-3 w-3" />
            الثقة
          </div>
          <p className="mt-0.5 text-sm font-bold text-[var(--status-success-text)]">
            %{Math.round(recommendation.confidence * 100)}
          </p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2">
          <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
            <AlertTriangle className="h-3 w-3" />
            الأثر
          </div>
          <p className="mt-0.5 text-sm font-bold text-[var(--text-primary)] capitalize">
            {recommendation.expectedImpact}
          </p>
        </div>
      </div>

      {recommendation.risks.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-medium text-[var(--status-danger-text)]">المخاطر</p>
          <div className="space-y-0.5">
            {recommendation.risks.map((r, i) => (
              <div
                key={i}
                className="flex items-start gap-1.5 text-[10px] text-[var(--text-muted)]"
              >
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-[var(--status-danger-text)]" />
                {r}
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendation.alternatives.length > 0 && (
        <div className="border-t border-[var(--border-color)] pt-2">
          <p className="mb-1 text-[10px] font-medium text-[var(--text-muted)]">بدائل</p>
          {recommendation.alternatives.map((alt, i) => (
            <div key={i} className="flex items-center justify-between py-0.5">
              <span className="text-[10px] text-[var(--text-muted)]">{alt.actionLabel}</span>
              <span className="text-[10px] text-[var(--text-muted)]">
                %{Math.round(alt.confidence * 100)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
