"use client";

import Link from "next/link";
import { EnrichmentPanel } from "@/features/gtm/EnrichmentPanel";

/**
 * FE-S11-05 — GTM Enrichment Waterfall (tip STORY-11-05).
 * ≥2 FakeEnrichment providers. Not Production GO / RAG GO.
 */
export default function EnrichmentPage() {
  return (
    <div className="space-y-6 p-6" data-testid="enrichment-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Enrichment Waterfall</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Multi-provider firmographic/contact fill via tip POST/GET /api/v1/gtm/enrichment. First
          non-empty value wins per field.
        </p>
      </div>
      <EnrichmentPanel />
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link href="/gtm" className="underline" data-testid="enrichment-hub-link">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
