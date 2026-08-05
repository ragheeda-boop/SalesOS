"use client";

import Link from "next/link";
import { TerritoriesStudio } from "@/features/tenant-studio/TerritoriesStudio";

/**
 * FE-S10-05 — Tenant Studio territory rules (tip STORY-10-05).
 * In-memory over CAP-017. Not Production GO / RAG GO.
 */
export default function TerritoriesStudioPage() {
  return (
    <div className="space-y-6 p-6" data-testid="territories-studio-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Territories Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Geography / industry / size territory rules via tip /api/v1/studio/territories. Unmatched
          does not invent a key. Live revenue DB / 141221 not claimed.
        </p>
      </div>
      <TerritoriesStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/studio/scoring" className="underline" data-testid="territories-scoring-link">
          /studio/scoring
        </Link>
        .
      </p>
    </div>
  );
}
