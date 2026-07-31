"use client";

import type { EmailMetricsDTO } from "@/lib/api/types";

interface EmailIntelligenceViewProps {
  metrics: EmailMetricsDTO | null;
  isLoading: boolean;
  error: Error | null;
  onRefresh: () => void;
}

export function EmailIntelligenceView({
  metrics,
  isLoading,
  error,
  onRefresh,
}: EmailIntelligenceViewProps) {
  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center h-full"
        role="status"
        aria-label="جار التحميل"
      >
        <div className="flex flex-col items-center gap-3 text-muted">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span>جاري تحميل تحليلات البريد...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full" role="alert">
        <div className="flex flex-col items-center gap-3 text-destructive">
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <span>تعذر تحميل تحليلات البريد</span>
          <button onClick={onRefresh} className="text-sm underline">
            إعادة المحاولة
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-full text-muted">
        لا توجد بيانات بريد إلكتروني
      </div>
    );
  }

  const replyRatePct = Math.round(metrics.reply_rate * 100);

  return (
    <div className="p-4 h-full flex flex-col gap-4" dir="rtl">
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="مرسل"
          value={metrics.total_sent}
          color="text-blue-400"
        />
        <StatCard
          label="مستلم"
          value={metrics.total_received}
          color="text-green-400"
        />
        <StatCard
          label="معدل الرد"
          value={`${replyRatePct}%`}
          color="text-[var(--status-warning-text)]"
        />
        <StatCard
          label="متوسط الرد"
          value={
            metrics.avg_response_hours != null
              ? `${metrics.avg_response_hours}h`
              : "-"
          }
          color="text-[var(--chart-purple)]"
        />
      </div>

      {metrics.top_companies && metrics.top_companies.length > 0 && (
        <div className="flex-1 min-h-0">
          <h4 className="text-xs font-semibold text-muted mb-2">
            أكثر الشركات تواصلاً
          </h4>
          <div className="space-y-1">
            {metrics.top_companies.slice(0, 5).map((c, i) => (
              <div
                key={c.company_id || i}
                className="flex justify-between text-sm"
              >
                <span className="truncate">{c.company_id}</span>
                <span className="text-muted tabular-nums">{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="bg-surface-elevated rounded-lg p-3 text-center">
      <div className={`text-2xl font-bold ${color} tabular-nums`}>{value}</div>
      <div className="text-xs text-muted mt-1">{label}</div>
    </div>
  );
}
