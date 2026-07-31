"use client";

import Link from "next/link";
import type { ActivityRecord } from "@/lib/api";
import { formatWhen } from "./format";
import {
  EmptyState,
  ErrorState,
  GhostButtonLink,
  LoadingState,
} from "./states";

function actionLabel(action: string): string {
  return action.replace(/[._]/g, " ");
}

function entityHref(entityType: string, entityId: string): string | null {
  switch (entityType) {
    case "company":
      return `/v3/companies/${entityId}`;
    case "contact":
      return `/v3/contacts/${entityId}`;
    case "opportunity":
    case "deal":
      return `/v3/crm/${entityId}`;
    case "employee":
    case "person":
      return `/v3/people/${entityId}`;
    default:
      return null;
  }
}

export function ActivityFeed({
  items,
  isLoading,
  isError,
  errorMessage,
  onRetry,
  emptyTitle = "No activity yet",
  emptyDescription = "When activity is recorded for this scope, it will show here. Empty is honest — nothing is invented.",
  emptyActionHref,
  emptyActionLabel,
  showEntity = false,
}: {
  items: ActivityRecord[];
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionHref?: string;
  emptyActionLabel?: string;
  showEntity?: boolean;
}) {
  if (isLoading) {
    return <LoadingState label="Loading activity…" />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Could not load activity"
        description={errorMessage || "Request failed"}
        onRetry={onRetry}
      />
    );
  }

  if (!items.length) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={
          emptyActionHref && emptyActionLabel ? (
            <GhostButtonLink href={emptyActionHref}>
              {emptyActionLabel}
            </GhostButtonLink>
          ) : undefined
        }
      />
    );
  }

  return (
    <ul className="divide-y divide-[var(--border-default)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
      {items.map((row) => {
        const href = showEntity
          ? entityHref(row.entity_type, row.entity_id)
          : null;
        return (
          <li key={row.id} className="px-3 py-2.5 text-sm">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="font-medium capitalize text-[var(--text-primary)]">
                {actionLabel(row.action)}
              </p>
              <p className="text-[12px] text-[var(--text-muted)]">
                {formatWhen(row.timestamp)}
              </p>
            </div>
            <p className="mt-0.5 text-[12px] text-[var(--text-secondary)]">
              {row.actor || "—"}
              {showEntity ? (
                <>
                  {" · "}
                  {href ? (
                    <Link
                      href={href}
                      className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
                    >
                      {row.entity_type} {row.entity_id.slice(0, 8)}
                    </Link>
                  ) : (
                    <span>
                      {row.entity_type} {row.entity_id.slice(0, 8)}
                    </span>
                  )}
                </>
              ) : null}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
