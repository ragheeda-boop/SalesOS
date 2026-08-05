import { type ReactNode } from "react";
import { cn } from "./utils";
import { Button } from "./button";

interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: EmptyStateAction;
  learnMoreLink?: string;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  learnMoreLink,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 py-16 text-center",
        "rtl:text-right",
        className
      )}
      role="status"
    >
      {icon && (
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--bg-secondary)] text-[var(--text-muted)]">
          {icon}
        </div>
      )}
      <div className="max-w-sm">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
        {description && <p className="mt-2 text-sm text-[var(--text-muted)]">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        {action && (
          <Button onClick={action.onClick} size="sm">
            {action.label}
          </Button>
        )}
        {learnMoreLink && (
          <a
            href={learnMoreLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-[var(--muhide-orange)] hover:underline"
          >
            Learn more
          </a>
        )}
      </div>
    </div>
  );
}
