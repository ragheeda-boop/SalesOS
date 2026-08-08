"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { Sparkles, ThumbsUp, ThumbsDown } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface NBAAcceptanceWidgetProps {
  nba_views: number;
  nba_accepts: number;
  nba_rejects: number;
  acceptance_rate: number;
}

export function NBAAcceptanceWidget({
  nba_views,
  nba_accepts,
  nba_rejects,
  acceptance_rate,
}: NBAAcceptanceWidgetProps) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-[var(--text-muted)]" />
        <p className="text-xs text-[var(--text-muted)]">{t("cs.nba_acceptance")}</p>
      </div>
      <p className="text-lg font-bold">{nba_views}</p>
      <p className="text-[10px] text-[var(--text-muted)]">{t("cs.total_views")}</p>
      <div className="flex items-center gap-3 mt-2 text-xs">
        <span className="flex items-center gap-1 text-[var(--status-success-text)]">
          <ThumbsUp className="h-3 w-3" /> {nba_accepts}
        </span>
        <span className="flex items-center gap-1 text-[var(--status-danger-text)]">
          <ThumbsDown className="h-3 w-3" /> {nba_rejects}
        </span>
      </div>
      <div className="mt-2 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
        <div
          className="h-full bg-green-500 rounded-full transition-all"
          style={{ width: `${acceptance_rate}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-[var(--text-muted)]">
        {t("cs.acceptance_rate", { rate: acceptance_rate.toFixed(0) })}
      </p>
    </div>
  );
}
