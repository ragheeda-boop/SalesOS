"use client";

import { cn } from "@salesos/ui";
import { Sparkles, Lightbulb, AlertTriangle, TrendingUp } from "lucide-react";
import type { AIAnswer } from "@salesos/search";

interface AIAnswerCardProps {
  answer: AIAnswer;
  className?: string;
}

export function AIAnswerCard({ answer, className }: AIAnswerCardProps) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--chart-purple-bg)] dark:border-[var(--border-strong)] dark:bg-[var(--bg-primary)]/10",
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b border-[var(--border-default)] px-4 py-2 dark:border-[var(--border-strong)]">
        <Sparkles className="h-4 w-4 text-[var(--chart-purple)]" />
        <span className="text-xs font-semibold text-[var(--text-secondary)] dark:text-[var(--text-muted)]">
          AI Answer
        </span>
        <span className="mr-auto text-[10px] text-[var(--chart-purple)]">
          %{Math.round(answer.confidence * 100)} ثقة
        </span>
      </div>
      <div className="space-y-3 px-4 py-3">
        <p className="text-sm leading-relaxed text-[var(--text-primary)] dark:text-[var(--text-primary)]">
          {answer.summary}
        </p>

        {answer.explanation && (
          <div className="flex items-start gap-2">
            <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--status-warning-text)]" />
            <p className="text-xs text-[var(--text-primary)] dark:text-[var(--text-disabled)]">
              {answer.explanation}
            </p>
          </div>
        )}

        {answer.recommendations && answer.recommendations.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)] dark:text-[var(--text-muted)]">
              <TrendingUp className="h-3.5 w-3.5" />
              توصيات
            </div>
            <ul className="mt-1 space-y-1">
              {answer.recommendations.map((r, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-xs text-[var(--text-primary)] dark:text-[var(--text-disabled)]"
                >
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--chart-purple)]" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {answer.risks && answer.risks.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--status-danger-text)]">
              <AlertTriangle className="h-3.5 w-3.5" />
              مخاطر
            </div>
            <ul className="mt-1 space-y-1">
              {answer.risks.map((r, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-xs text-[var(--status-danger-text)]"
                >
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--status-danger-text)]" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {answer.sources.length > 0 && (
          <div className="border-t border-[var(--border-default)] pt-2 dark:border-[var(--border-strong)]">
            <p className="text-[10px] font-medium text-[var(--chart-purple)] dark:text-[var(--chart-purple)]">
              المصادر:
            </p>
            <div className="mt-1 flex flex-wrap gap-1">
              {answer.sources.map((s, i) => (
                <span
                  key={i}
                  className="rounded-full bg-[var(--chart-purple-bg)] px-2 py-0.5 text-[10px] text-[var(--text-secondary)] dark:bg-[var(--bg-primary)]/50 dark:text-[var(--text-muted)]"
                >
                  {s.title}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
