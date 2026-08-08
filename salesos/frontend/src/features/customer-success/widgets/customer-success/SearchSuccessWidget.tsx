"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { Search, TrendingUp, AlertCircle } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface SearchSuccessWidgetProps {
  total_searches: number;
  searches_with_action: number;
  success_rate: number;
}

export function SearchSuccessWidget({
  total_searches,
  searches_with_action,
  success_rate,
}: SearchSuccessWidgetProps) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <Search className="h-4 w-4 text-[var(--text-muted)]" />
        <p className="text-xs text-[var(--text-muted)]">{t("cs.search_success")}</p>
      </div>
      <p className="text-lg font-bold">{total_searches}</p>
      <div className="flex items-center gap-1 mt-1">
        {success_rate >= 50 ? (
          <TrendingUp className="h-3 w-3 text-[var(--status-success-text)]" />
        ) : (
          <AlertCircle className="h-3 w-3 text-yellow-500" />
        )}
        <span className="text-xs text-[var(--text-muted)]">
          {t("cs.actions_from_searches", {
            actions: searches_with_action,
            total: total_searches,
          })}
        </span>
      </div>
      <div className="mt-2 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
        <div
          className="h-full bg-orange-500 rounded-full transition-all"
          style={{ width: `${success_rate}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-[var(--text-muted)]">
        {t("cs.success_rate", { rate: success_rate.toFixed(0) })}
      </p>
    </div>
  );
}
