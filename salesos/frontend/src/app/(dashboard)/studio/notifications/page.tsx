"use client";

import Link from "next/link";
import { NotificationRulesStudio } from "@/features/tenant-studio/NotificationRulesStudio";

/**
 * FE-S10-08 — Tenant Studio notification rules (tip STORY-10-08).
 * RulesEngine send_notification. Not Production GO / RAG GO.
 */
export default function NotificationRulesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="notification-rules-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Notification Rules Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Route tenant events to in_app / email via tip RulesEngine send_notification compile path.
        </p>
      </div>
      <NotificationRulesStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/studio/workflows"
          className="underline"
          data-testid="notification-workflows-link"
        >
          /studio/workflows
        </Link>
        .
      </p>
    </div>
  );
}
