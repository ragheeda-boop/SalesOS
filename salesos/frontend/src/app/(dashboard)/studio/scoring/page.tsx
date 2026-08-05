"use client";

import Link from "next/link";
import { ScoringRulesStudio } from "@/features/tenant-studio/ScoringRulesStudio";

/**
 * FE-S10-04 — Tenant Studio scoring rules (tip STORY-10-04).
 * Deterministic in-memory. Not Production GO / RAG GO.
 */
export default function ScoringRulesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="scoring-rules-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Scoring Rules Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Override platform dimension weights and attribute boosts against tip Tenant Studio HTTP.
          Fail-safe falls back to platform default on rule error.
        </p>
      </div>
      <ScoringRulesStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/studio/custom-fields"
          className="underline"
          data-testid="scoring-rules-custom-fields-link"
        >
          /studio/custom-fields
        </Link>
        .
      </p>
    </div>
  );
}
