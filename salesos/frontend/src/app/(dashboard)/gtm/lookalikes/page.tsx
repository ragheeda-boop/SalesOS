"use client";

import Link from "next/link";
import { LookalikePanel } from "@/features/gtm/LookalikePanel";

/**
 * FE-S11-04 — GTM Lookalike Accounts (tip STORY-11-04).
 * Deterministic won/lost fixtures. Not Production GO / RAG GO.
 */
export default function LookalikePage() {
  return (
    <div className="space-y-6 p-6" data-testid="lookalike-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Lookalike Accounts</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Rank similar accounts from tip POST/GET /api/v1/gtm/lookalikes using won/lost
          Opportunity-shaped history (CI fixtures — not live ML).
        </p>
      </div>
      <LookalikePanel />
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link href="/gtm" className="underline" data-testid="lookalike-hub-link">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
