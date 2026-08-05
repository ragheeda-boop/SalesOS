"use client";

import { useState } from "react";
import { cn } from "@salesos/ui";
import { Sparkles, Check, X } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { ConfidenceBadge, getConfidenceLevel } from "./ConfidenceBadge";
import type { InlineSuggestionData } from "./types";

interface InlineSuggestionProps {
  suggestion: InlineSuggestionData;
  onDismiss: (id: string) => void;
  onApply?: (id: string) => void;
}

export function InlineSuggestion({ suggestion, onDismiss, onApply }: InlineSuggestionProps) {
  const { t } = useTranslation();
  const [applied, setApplied] = useState(false);

  const handleApply = () => {
    setApplied(true);
    onApply?.(suggestion.id);
  };

  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2 transition-all",
        applied
          ? "border-success-200 bg-success-50 dark:border-success-800 dark:bg-success-900/20"
          : "border-[var(--muhide-orange)]/30 bg-[var(--muhide-orange)]/5"
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Sparkles className="h-3 w-3 shrink-0 text-[var(--muhide-orange)]" />
          <span className="text-xs text-[var(--text-secondary)] truncate">
            {suggestion.content}
          </span>
          <ConfidenceBadge
            level={suggestion.confidenceLevel}
            score={suggestion.confidence}
            className="shrink-0"
          />
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {!applied && onApply && (
            <button
              onClick={handleApply}
              className="rounded-md p-1 text-success-600 hover:bg-success-100 dark:hover:bg-success-900/30 transition-colors"
              aria-label={t("ai_insights.apply")}
            >
              <Check className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={() => onDismiss(suggestion.id)}
            className="rounded-md p-1 text-[var(--text-disabled)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] transition-colors"
            aria-label={t("ai_insights.dismiss")}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
