"use client";

import Link from "next/link";
import { PermissionsStudio } from "@/features/tenant-studio/PermissionsStudio";

/**
 * FE-S10-06 — Tenant Studio permissions / custom roles (tip STORY-10-06).
 * Entitlement ceiling. Not Production GO / RAG GO.
 */
export default function PermissionsStudioPage() {
  return (
    <div className="space-y-6 p-6" data-testid="permissions-studio-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Permissions Studio</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Define tenant-custom roles capped at Plan.entitlements ceiling against tip Tenant Studio
          HTTP. Privilege escalation is blocked (403).
        </p>
      </div>
      <PermissionsStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link href="/studio/scoring" className="underline" data-testid="permissions-scoring-link">
          /studio/scoring
        </Link>
        .
      </p>
    </div>
  );
}
