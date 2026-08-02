"use client";

import Link from "next/link";
import { MarketplaceListingsBrowse } from "@/features/marketplace-listings/MarketplaceListingsBrowse";

/**
 * FE-S13-01b — tip MarketplaceListing browse (STORY-13-01).
 * Separate from CAP-036 plugin stub at /marketplace. No install/certify.
 */
export default function MarketplaceListingsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="marketplace-listings-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Marketplace Listings
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Read-only tip catalog against /api/v1/marketplace/listings (memory).
          Not the CAP-036 plugin stub. No install or certify UI yet.
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
