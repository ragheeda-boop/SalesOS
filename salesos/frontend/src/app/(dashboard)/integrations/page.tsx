"use client";

import Link from "next/link";
import { IntegrationsStudio } from "@/features/integrations/IntegrationsStudio";
import { SecondConnectorCertPanel } from "@/features/integrations/SecondConnectorCertPanel";

/**
 * STORY-08-07 + FE-S11-10 — Tenant Integrations Studio + tip certify.
 * Hub HTTP from STORY-08-06 / 11-10. Not Production GO.
 */
export default function IntegrationsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="integrations-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Integrations Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Connect, test, map, schedule, monitor, and disconnect Integration Hub connections for this
          tenant. Live HubSpot network is not claimed.
        </p>
      </div>
      <SecondConnectorCertPanel />
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
