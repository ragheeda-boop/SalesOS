"use client";

import { cn } from "@salesos/ui";
import {
  Sparkles,
  Lightbulb,
  ExternalLink,
  X,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { ConfidenceBadge, getConfidenceLevel } from "./ConfidenceBadge";
import type { ContextualInsightData } from "./types";

interface ContextualInsightProps {
  insight: ContextualInsightData;
  onDismiss: (id: string) => void;
}

export function ContextualInsight({ insight, onDismiss }: ContextualInsightProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        "group relative rounded-xl border p-4",
        "border-[var(--border-default)] bg-[var(--bg-primary)]",
        "shadow-muhide-1 hover:shadow-muhide-2 transition-shadow",
      )}
    >
      <button
        onClick={() => onDismiss(insight.id)}
        className="absolute inset-inline-end-2 top-2 rounded-md p-1 text-[var(--text-disabled)] opacity-0 hover:text-[var(--text-secondary)] group-hover:opacity-100 transition-opacity"
        aria-label={t("ai_insights.dismiss")}
      >
        <X className="h-3.5 w-3.5" />
      </button>

      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--chart-purple-bg)] text-[var(--chart-purple)]">
          <Lightbulb className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-[var(--text-primary)] truncate">
              {insight.title}
            </h4>
            <ConfidenceBadge
              level={insight.confidenceLevel}
              score={insight.confidence}
            />
          </div>
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            {insight.content}
          </p>

          {insight.suggestion && (
            <div className="flex items-start gap-2 rounded-lg bg-[var(--bg-secondary)] px-3 py-2">
              <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--muhide-orange)]" />
              <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                {insight.suggestion}
              </p>
            </div>
          )}

          {insight.action && (
            <a
              href={insight.action.href}
              className="inline-flex items-center gap-1 text-xs font-medium text-[var(--muhide-orange)] hover:underline"
            >
              {insight.action.label}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
