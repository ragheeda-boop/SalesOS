"use client";

import Link from "next/link";
import { IcpProfilesPanel } from "@/features/gtm/IcpProfilesPanel";

/**
 * FE-S11-01 — GTM ICP Profiles (tip STORY-11-01).
 * Versioned ICP + deterministic score. Not Production GO / RAG GO.
 */
export default function IcpProfilesPage() {
  return (
    <div className="space-y-6 p-6" data-testid="icp-profiles-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">ICP Profiles</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Versioned reusable ICPProfile via tip POST/GET/PUT /api/v1/gtm/icp-profiles (+ score).
        </p>
      </div>
      <IcpProfilesPanel />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/gtm" className="underline" data-testid="icp-gtm-hub-link">
          /gtm
        </Link>
        .
      </p>
    </div>
  );
}
