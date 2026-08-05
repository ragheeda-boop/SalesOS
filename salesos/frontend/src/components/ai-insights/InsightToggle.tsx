"use client";

import { cn } from "@salesos/ui";
import { useTranslation } from "@/lib/i18n";

interface InsightToggleProps {
  showLowConfidence: boolean;
  onChange: (value: boolean) => void;
  className?: string;
}

export function InsightToggle({ showLowConfidence, onChange, className }: InsightToggleProps) {
  const { t } = useTranslation();

  return (
    <label className={cn("flex items-center gap-2 cursor-pointer select-none", className)}>
      <button
        type="button"
        role="switch"
        aria-checked={showLowConfidence}
        onClick={() => onChange(!showLowConfidence)}
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors",
          showLowConfidence ? "bg-[var(--muhide-orange)]" : "bg-[var(--bg-tertiary)]"
        )}
      >
        <span
          className={cn(
            "pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform",
            showLowConfidence ? "translate-x-4" : "translate-x-0"
          )}
        />
      </button>
      <span className="text-xs text-[var(--text-secondary)]">
        {t("ai_insights.show_low_confidence")}
      </span>
    </label>
  );
}
