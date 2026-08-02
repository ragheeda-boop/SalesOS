"use client";

import Link from "next/link";
import { BrandingStudio } from "@/features/tenant-studio/BrandingStudio";

/**
 * FE-S10-07 — Tenant Studio branding (tip STORY-10-07).
 * Logo URL / colors / name / locales. Not Production GO / RAG GO.
 */
export default function BrandingStudioPage() {
  return (
    <div className="space-y-6 p-6" data-testid="branding-studio-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Branding & Languages Studio
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tenant display name, logo URL, colors, and ar/en locales via tip
          GET/PUT /api/v1/studio/branding.
        </p>
      </div>
      <BrandingStudio />
      <p className="text-xs text-[var(--text-muted)]">
        Related:{" "}
        <Link
          href="/studio/custom-fields"
          className="underline"
          data-testid="branding-custom-fields-link"
        >
          /studio/custom-fields
        </Link>
        .
      </p>
    </div>
  );
}
