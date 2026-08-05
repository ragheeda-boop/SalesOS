"use client";

import { cn } from "@salesos/ui";
import { AlertCircle, RefreshCw } from "lucide-react";

interface SearchErrorProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function SearchError({ message = "فشل البحث", onRetry, className }: SearchErrorProps) {
  return (
    <div
      role="alert"
      className={cn("flex flex-col items-center justify-center py-12 text-center", className)}
    >
      <AlertCircle className="mb-3 h-10 w-10 text-[var(--status-danger-text)]" />
      <p className="text-sm font-medium text-[var(--status-danger-text)]">{message}</p>
      <p className="mt-1 text-xs text-[var(--text-muted)]">حدث خطأ أثناء البحث. حاول مرة أخرى.</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-primary-600 hover:bg-primary-50 dark:text-primary-400 dark:hover:bg-primary-900/20"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          إعادة المحاولة
        </button>
      )}
    </div>
  );
}
