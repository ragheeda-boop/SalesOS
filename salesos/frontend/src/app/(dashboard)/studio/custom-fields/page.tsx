"use client";

import Link from "next/link";
import { CustomFieldsStudio } from "@/features/tenant-studio/CustomFieldsStudio";

/**
 * FE-S10-01 — Tenant Studio custom field definitions (tip STORY-10-01).
 * Not Production GO / RAG GO. Auto-render is STORY-10-02.
 */
export default function CustomFieldsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="custom-fields-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Custom Fields Studio
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Define versioned scalar custom fields for company / contact /
          opportunity against tip Tenant Studio HTTP.
        </p>
      </div>
      <CustomFieldsStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/integrations"
          className="underline"
          data-testid="custom-fields-integrations-link"
        >
          /integrations
        </Link>
        .
      </p>
    </div>
  );
}
