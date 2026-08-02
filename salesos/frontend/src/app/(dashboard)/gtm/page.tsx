"use client";

import { GtmHub } from "@/features/gtm/GtmHub";

/**
 * FE-S11-03b — GTM Intelligence hub (tip STORY-11-02/03 pages).
 * Not Production GO / RAG GO. ICP / territories not invented.
 */
export default function GtmHubPage() {
  return (
    <div className="space-y-6 p-6" data-testid="gtm-hub-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          GTM Intelligence
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip market sizing and lead discovery — no invented ICP or territories.
        </p>
      </div>
      <GtmHub />
    </div>
  );
}
