"use client";

import Link from "next/link";
import { IntegrationsStudio } from "@/features/integrations/IntegrationsStudio";

/**
 * STORY-08-07 — Tenant Integrations Studio (DOM-021).
 * Hub HTTP from STORY-08-06. Not Production GO.
 */
export default function IntegrationsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="integrations-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Integrations Studio
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Connect, test, map, schedule, monitor, and disconnect Integration Hub
          connections for this tenant.
        </p>
      </div>
      <IntegrationsStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Owner inventory:{" "}
        <Link
          href="/admin/integrations"
          className="underline"
          data-testid="integrations-admin-inventory-link"
        >
          /admin/integrations
        </Link>
        .
      </p>
    </div>
  );
}
