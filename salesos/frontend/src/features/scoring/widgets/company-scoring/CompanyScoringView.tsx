"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import type { Score, Recommendation } from "@salesos/decision-platform";

interface CompanyScoringViewProps {
  dealScore: number;
  scores: Score[];
  recommendations: Recommendation[];
  riskFlags: Score[];
  isLoading: boolean;
  error: Error | null;
  onRefresh: () => void;
}

export function CompanyScoringView({
  dealScore,
  scores,
  recommendations,
  riskFlags,
  isLoading,
  error,
  onRefresh,
}: CompanyScoringViewProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full" role="status">
        <div className="flex flex-col items-center gap-3 text-muted">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span>جاري تحميل التقييمات...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-destructive" role="alert">
        <div className="flex flex-col items-center gap-3">
          <span>تعذر تحميل التقييمات</span>
          <button onClick={onRefresh} className="text-sm underline">
            إعادة المحاولة
          </button>
        </div>
      </div>
    );
  }

  if (!dealScore && !scores.length && !recommendations.length) {
    return (
      <div className="flex items-center justify-center h-full text-muted">
        لا توجد تقييمات متاحة
      </div>
    );
  }

  const gaugeColor =
    dealScore >= 70 ? "stroke-green-500" : dealScore >= 40 ? "stroke-amber-500" : "stroke-red-500";
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (dealScore / 100) * circumference;

  return (
    <div className="p-4 h-full flex flex-col gap-4" dir="rtl">
      <div className="flex items-center gap-4">
        <div className="relative shrink-0">
          <svg className="h-20 w-20 -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-[var(--text-disabled)]"
            />
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              className={gaugeColor}
              strokeDasharray={`${offset} ${circumference}`}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-[var(--text-primary)]">
              {Math.round(dealScore)}
            </span>
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-[var(--text-primary)]">درجة الصفقة</p>
          <p className="text-xs text-[var(--text-muted)]">
            {dealScore >= 70
              ? "جاهزة للإغلاق"
              : dealScore >= 40
                ? "في طور التقييم"
                : "تحتاج متابعة"}
          </p>
        </div>
      </div>

      {scores.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-[var(--text-muted)]">عوامل التقييم</h4>
          {scores.slice(0, 5).map((s) => (
            <div key={s.name || s.label}>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-secondary)]">{s.label || s.name}</span>
                <span className="text-[var(--text-primary)]">{Math.round(s.value * 100)}%</span>
              </div>
              <div className="mt-1 h-1.5 w-full rounded-full bg-[var(--bg-tertiary)]">
                <div
                  className="h-full rounded-full bg-[var(--muhide-orange)]"
                  style={{ width: `${Math.min(100, s.value * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="space-y-1.5">
          <h4 className="text-xs font-semibold text-[var(--text-muted)]">التوصيات</h4>
          {recommendations.slice(0, 3).map((rec, i) => (
            <div
              key={rec.id || String(i)}
              className="rounded-lg border border-[var(--border-default)] p-2 text-xs"
            >
              <p className="font-medium text-[var(--text-primary)]">
                {rec.actionLabel ?? rec.action}
              </p>
              {rec.reason && <p className="mt-0.5 text-[var(--text-muted)]">{rec.reason}</p>}
            </div>
          ))}
        </div>
      )}

      {riskFlags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {riskFlags.map((flag, i) => (
            <span
              key={i}
              className="rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] text-red-500"
            >
              {flag.label || flag.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
