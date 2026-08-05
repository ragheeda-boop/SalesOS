"use client";

import { cn } from "@salesos/ui";

interface SearchBadgeProps {
  label: string;
  variant?: "info" | "success" | "warning" | "danger" | "neutral";
  className?: string;
}

const VARIANT_STYLE: Record<string, string> = {
  info: "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  success: "bg-[var(--status-success-bg)] text-[var(--status-success-text)]",
  warning: "bg-[var(--status-warning-bg)] text-amber-700",
  danger: "bg-[var(--status-danger-bg)] text-red-700",
  neutral: "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
};

export function SearchBadge({ label, variant = "neutral", className }: SearchBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
        VARIANT_STYLE[variant],
        className
      )}
    >
      {label}
    </span>
  );
}
