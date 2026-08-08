"use client";

import type { FollowupDashboardDTO, FollowUpStatusDTO } from "@/lib/api/types";

interface FollowupCenterViewProps {
  followups: FollowupDashboardDTO | null;
  isLoading: boolean;
  error: Error | null;
  onRefresh: () => void;
}

export function FollowupCenterView({
  followups,
  isLoading,
  error,
  onRefresh,
}: FollowupCenterViewProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full" role="status">
        <div className="flex flex-col items-center gap-3 text-muted">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span>جاري تحميل المتابعات...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-destructive" role="alert">
        <div className="flex flex-col items-center gap-3">
          <span>تعذر تحميل المتابعات</span>
          <button onClick={onRefresh} className="text-sm underline">
            إعادة المحاولة
          </button>
        </div>
      </div>
    );
  }

  if (!followups) {
    return (
      <div className="flex items-center justify-center h-full text-muted">لا توجد متابعات</div>
    );
  }

  return (
    <div className="p-4 h-full flex flex-col gap-4" dir="rtl">
      <div className="grid grid-cols-4 gap-2">
        <SummaryBadge
          label="الإجمالي"
          value={followups.total}
          color="bg-blue-500/20 text-blue-400"
        />
        <SummaryBadge label="متأخرة" value={followups.overdue} color="bg-red-500/20 text-red-400" />
        <SummaryBadge
          label="تحتاج متابعة"
          value={followups.need_followup}
          color="bg-amber-500/20 text-[var(--status-warning-text)]"
        />
        <SummaryBadge
          label="بانتظارك"
          value={followups.waiting_you}
          color="bg-[var(--chart-purple)]/20 text-[var(--chart-purple)]"
        />
      </div>

      {followups.items && followups.items.length > 0 ? (
        <div className="flex-1 min-h-0 overflow-auto space-y-1">
          {followups.items.map((item) => (
            <FollowupRow key={item.company_id} item={item} />
          ))}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-muted text-sm">
          جميع المتابعات محدثة
        </div>
      )}
    </div>
  );
}

function FollowupRow({ item }: { item: FollowUpStatusDTO }) {
  const priorityColors: Record<string, string> = {
    critical: "border-red-500 bg-red-500/5",
    high: "border-amber-500 bg-amber-500/5",
    medium: "border-blue-500 bg-blue-500/5",
    low: "border-transparent bg-transparent",
  };

  const labels: Record<string, string> = {
    waiting_you: "بانتظار ردك",
    waiting_customer: "بانتظار العميل",
    overdue: "متأخر",
    need_followup: "يحتاج متابعة",
  };

  const activeLabel = Object.entries(labels).find(
    ([key]) => (item as unknown as Record<string, boolean | undefined>)[key]
  )?.[1];

  return (
    <div
      className={`flex items-center justify-between p-2 rounded border-r-2 text-sm ${
        priorityColors[item.priority] || priorityColors.low
      }`}
    >
      <span className="truncate font-medium">{item.company_id.slice(0, 12)}</span>
      <div className="flex items-center gap-2 shrink-0">
        {activeLabel && <span className="text-xs text-muted">{activeLabel}</span>}
        {item.last_outbound_days != null && (
          <span className="text-xs tabular-nums text-muted">{item.last_outbound_days} يوم</span>
        )}
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded uppercase ${
            item.priority === "critical"
              ? "bg-red-500/20 text-red-400"
              : item.priority === "high"
                ? "bg-amber-500/20 text-[var(--status-warning-text)]"
                : "bg-blue-500/20 text-blue-400"
          }`}
        >
          {item.priority}
        </span>
      </div>
    </div>
  );
}

function SummaryBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg p-2 text-center ${color}`}>
      <div className="text-lg font-bold tabular-nums">{value}</div>
      <div className="text-[10px] opacity-70">{label}</div>
    </div>
  );
}
