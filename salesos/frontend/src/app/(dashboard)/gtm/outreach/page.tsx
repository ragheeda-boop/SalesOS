"use client";

import Link from "next/link";
import { Suspense } from "react";
import { Spinner } from "@salesos/ui";
import { OutreachPanel } from "@/features/gtm/OutreachPanel";

/**
 * FE-S11-08 — GTM AI Outreach (tip STORY-11-08).
 * Fixture generator; draft_only; feature_ai_copilot False. Not Production GO.
 */
export default function OutreachPage() {
  return (
    <div className="space-y-6 p-6" data-testid="outreach-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">AI Outreach</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip POST/GET /api/v1/gtm/outreach — fixture drafts only. No live SMTP / LinkedIn /
          WhatsApp. feature_ai_copilot remains False.
        </p>
      </div>
      <Suspense fallback={<Spinner />}>
        <OutreachPanel />
      </Suspense>
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link href="/gtm" className="underline" data-testid="outreach-hub-link">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
