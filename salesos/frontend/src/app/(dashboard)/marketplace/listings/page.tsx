"use client";

import Link from "next/link";
import { MarketplaceListingsBrowse } from "@/features/marketplace-listings/MarketplaceListingsBrowse";

/**
 * FE-S13-04 — tip MarketplaceListing browse + certify + publish/install.
 * Catalog install ≠ live ERP. Separate from CAP-036 stub.
 */
export default function MarketplaceListingsPage() {
  return (
    <div className="space-y-6 p-6" data-testid="marketplace-listings-page">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Marketplace Listings</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Tip memory catalog + certify/publish/catalog-install against /api/v1/marketplace/listings.
          Catalog install ≠ live HubSpot/Odoo sync. Not the CAP-036 plugin stub.
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
