"use client";

import Link from "next/link";
import { Suspense } from "react";
import { Spinner } from "@salesos/ui";
import { WebsiteIntelligencePanel } from "@/features/gtm/WebsiteIntelligencePanel";

/**
 * FE-S11-07 — GTM Website Intelligence (tip STORY-11-07).
 * Fixture analyzer; feature_ai_copilot False. Not Production GO / RAG GO.
 */
export default function WebsiteIntelligencePage() {
  return (
    <div className="space-y-6 p-6" data-testid="website-intel-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Website Intelligence
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip POST/GET /api/v1/gtm/website-intelligence — fixture analyzer +
          governed prompt. Live crawl / live LLM not claimed.
        </p>
      </div>
      <Suspense fallback={<Spinner />}>
        <WebsiteIntelligencePanel />
      </Suspense>
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link
          href="/gtm"
          className="underline"
          data-testid="website-intel-hub-link"
        >
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
