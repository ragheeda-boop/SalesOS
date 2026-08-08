"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { Users, Activity, CalendarDays } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface ActiveUsersWidgetProps {
  dau: number;
  wau: number;
  mau: number;
}

export function ActiveUsersWidget({ dau, wau, mau }: ActiveUsersWidgetProps) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <Users className="h-4 w-4 text-[var(--text-muted)]" />
        <p className="text-xs text-[var(--text-muted)]">{t("cs.active_users")}</p>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center">
          <p className="text-lg font-bold text-orange-500">{dau}</p>
          <p className="text-[10px] text-[var(--text-muted)] flex items-center justify-center gap-1">
            <Activity className="h-3 w-3" /> {t("cs.daily")}
          </p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-blue-500">{wau}</p>
          <p className="text-[10px] text-[var(--text-muted)] flex items-center justify-center gap-1">
            <CalendarDays className="h-3 w-3" /> {t("cs.weekly")}
          </p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-[var(--chart-purple)]">{mau}</p>
          <p className="text-[10px] text-[var(--text-muted)] flex items-center justify-center gap-1">
            <CalendarDays className="h-3 w-3" /> {t("cs.monthly")}
          </p>
        </div>
      </div>
    </div>
  );
}
