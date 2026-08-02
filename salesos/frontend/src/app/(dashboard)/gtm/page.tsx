"use client";

import { GtmHub } from "@/features/gtm/GtmHub";

/**
 * FE-S11-03b (+ honesty sync) — GTM Intelligence hub for tip GTM pages.
 * Tip ICP / lookalikes / enrichment / verification / sequences landed.
 * Territories Studio tip path: /studio/territories. Not Production GO / RAG GO.
 */
export default function GtmHubPage() {
  return (
    <div className="space-y-6 p-6" data-testid="gtm-hub-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          GTM Intelligence
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip GTM pages: ICP, market sizing, lead discovery, lookalikes,
          enrichment, verification, sequences. Territories Studio is tip
          /studio/territories. Live 141221 / live ERP not claimed. Not
          Production GO / RAG GO.
        </p>
      </div>
      <GtmHub />
    </div>
  );
}
