"use client";

import Link from "next/link";
import { SequencingPanel } from "@/features/gtm/SequencingPanel";

/** FE-S11-09 — tip STORY-11-09 email sequences. Not Production GO / RAG GO. */
export default function SequencesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="sequences-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Email Sequences
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Email-only SequenceDefinition + enrollment via tip
          /api/v1/gtm/sequences. Live SMTP / LinkedIn / WhatsApp not claimed.
        </p>
      </div>
      <SequencingPanel />
      <p className="text-xs text-[var(--text-muted)]">
        Hub:{" "}
        <Link
          href="/gtm"
          className="underline"
          data-testid="sequences-hub-link"
        >
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
