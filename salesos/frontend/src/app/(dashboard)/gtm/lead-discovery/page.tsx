"use client";

import Link from "next/link";
import { LeadDiscoveryPanel } from "@/features/gtm/LeadDiscoveryPanel";

/**
 * FE-S11-03 — GTM Lead Discovery (tip STORY-11-03).
 * Gov-first + Hub fallback. Not Production GO / RAG GO.
 */
export default function LeadDiscoveryPage() {
  return (
    <div className="space-y-6 p-6" data-testid="lead-discovery-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Lead Discovery
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Government-data-first sourcing with Integration Hub provider fallback
          via tip POST/GET /api/v1/gtm/lead-discovery.
        </p>
      </div>
      <LeadDiscoveryPanel />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/gtm/market-sizing"
          className="underline"
          data-testid="lead-discovery-market-sizing-link"
        >
          /gtm/market-sizing
        </Link>
        .
      </p>
    </div>
  );
}
