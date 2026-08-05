"use client";

import { MarketSizingPanel } from "@/features/gtm/MarketSizingPanel";

/**
 * FE-S11-02 — GTM TAM/SAM/SOM market sizing (tip STORY-11-02).
 * Gov-dataset-shaped in-memory universe. Not Production GO / RAG GO.
 */
export default function MarketSizingPage() {
  return (
    <div className="space-y-6 p-6" data-testid="market-sizing-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Market Sizing (TAM / SAM / SOM)
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Compute nested market bands via tip POST/GET /api/v1/gtm/market-sizing.
        </p>
      </div>
      <MarketSizingPanel />
    </div>
  );
}
