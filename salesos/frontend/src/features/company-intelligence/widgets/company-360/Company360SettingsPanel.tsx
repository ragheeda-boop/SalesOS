"use client";

import { Settings } from "lucide-react";
import { EmptyState } from "@salesos/ui";
import { asSettingsRows } from "./company360Lists";

export function Company360SettingsPanel({
  company360,
  company,
}: {
  company360: unknown;
  company?: unknown;
}) {
  const rows = asSettingsRows(company360, company);
  if (rows.length === 0) {
    return (
      <EmptyState
        icon={<Settings className="h-10 w-10" />}
        title="لا توجد بيانات إعدادات"
        description="لا يتوفر كائن إعدادات من الواجهة — ولا حقول شركة للعرض"
      />
    );
  }
  return (
    <div className="space-y-3" data-testid="company360-settings-panel">
      {rows.map((row) => (
        <div
          key={row.id}
          className="flex items-center justify-between gap-3 p-3 rounded-lg border border-[var(--border-default)]"
        >
          <div className="text-xs text-[var(--text-muted)] shrink-0">{row.label}</div>
          <div className="font-medium text-[var(--text-primary)] text-sm truncate text-end">
            {row.value}
          </div>
        </div>
      ))}
    </div>
  );
}
