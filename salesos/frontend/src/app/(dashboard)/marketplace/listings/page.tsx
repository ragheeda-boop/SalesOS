"use client";

import Link from "next/link";
import { MarketplaceListingsBrowse } from "@/features/marketplace-listings/MarketplaceListingsBrowse";

/**
 * FE-S13-03 — tip MarketplaceListing browse + CAP-094 certify (STORY-13-01/02).
 * Separate from CAP-036 plugin stub at /marketplace. No invented install HTTP.
 */
export default function MarketplaceListingsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="marketplace-listings-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Marketplace Listings
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip memory catalog + submit/certify against
          /api/v1/marketplace/listings. Not the CAP-036 plugin stub. Sandboxed
          trial is inside certify only — live HubSpot/Odoo sync not claimed.
        </p>
      </div>
      <MarketplaceListingsBrowse />
      <p className="text-xs text-[var(--text-muted)]">
        Legacy plugin stub (CAP-036):{" "}
        <Link
          href="/marketplace"
          className="underline"
          data-testid="marketplace-listings-stub-link"
        >
          /marketplace
        </Link>
        . Related:{" "}
        <Link href="/integrations" className="underline">
          /integrations
        </Link>
        .
      </p>
    </div>
  );
}
