"use client";

import Link from "next/link";
import { SequencingPanel } from "@/features/gtm/SequencingPanel";

/** FE-S11-09 / 09b — tip sequences (email + partner LI/WA). Not Production GO. */
export default function SequencesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="sequences-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Sequences
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip /api/v1/gtm/sequences — email + partner LinkedIn/WhatsApp channel
          shapes. Live SMTP / LinkedIn / WhatsApp network not claimed.
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
