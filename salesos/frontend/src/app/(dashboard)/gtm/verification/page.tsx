"use client";

import Link from "next/link";
import { VerificationPanel } from "@/features/gtm/VerificationPanel";

/**
 * FE-S11-06 — GTM Contact Verification (tip STORY-11-06).
 * fake_verify connector. Not Production GO / RAG GO.
 */
export default function VerificationPage() {
  return (
    <div className="space-y-6 p-6" data-testid="verification-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Contact Verification</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Email/phone channel verdicts via tip POST/GET /api/v1/gtm/verification. Single
          VerificationConnector swap-in.
        </p>
      </div>
      <VerificationPanel />
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link href="/gtm" className="underline" data-testid="verification-hub-link">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
