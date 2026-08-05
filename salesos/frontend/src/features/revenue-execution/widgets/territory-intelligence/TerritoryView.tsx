"use client";

import { cn } from "@salesos/ui";
import { MapPin, AlertTriangle } from "lucide-react";
import type { TerritoryData } from "./types";

export function TerritoryView({ data }: { data: TerritoryData }) {
  return (
    <div role="region" aria-label="ذكاء المناطق" className="space-y-3/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-2 gap-2">
        {data.territories.map((t) => (
          <div key={t.id} className="rounded-lg bg-[var(--bg-tertiary)] p-2">
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3 text-[var(--text-muted)]" />
              <span className="text-[10px] font-medium text-[var(--text-primary)]">{t.name}</span>
            </div>
            <p className="mt-0.5 text-lg font-bold text-[var(--text-primary)]">
              $
              {t.value >= 1e6 ? (t.value / 1e6).toFixed(1) + "M" : (t.value / 1e3).toFixed(0) + "K"}
            </p>
            <div className="mt-1 h-1.5 w-full rounded-full bg-[var(--bg-tertiary)]">
              <div
                className={cn(
                  "h-full rounded-full",
                  t.attainment >= 80
                    ? "bg-green-500"
                    : t.attainment >= 50
                      ? "bg-amber-500"
                      : "bg-red-500"
                )}
                style={{ width: `${t.attainment}%` }}
              />
            </div>
            <p className="mt-0.5 text-[9px] text-[var(--text-muted)]">
              %{t.attainment} من الهدف · {t.deals} صفقات
            </p>
          </div>
        ))}
      </div>
      {data.gaps.length > 0 && (
        <div>
          <p className="mb-1 flex items-center gap-1 text-[10px] font-medium text-[var(--status-warning-text)]">
            <AlertTriangle className="h-3 w-3" /> فجوات التغطية
          </p>
          {data.gaps.map((g, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg bg-[var(--status-warning-bg)]/50 px-2 py-1"
            >
              <span className="text-[10px] text-[var(--text-primary)]">{g.region}</span>
              <span className="text-[9px] text-[var(--text-muted)]">
                {g.reason} · $
                {g.potentialValue >= 1e6
                  ? (g.potentialValue / 1e6).toFixed(1) + "M"
                  : (g.potentialValue / 1e3).toFixed(0) + "K"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
