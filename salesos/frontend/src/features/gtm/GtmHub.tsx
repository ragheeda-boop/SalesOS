"use client";

import Link from "next/link";
import {
  LEAD_DISCOVERY_HONESTY,
  LEAD_DISCOVERY_NON_GOALS,
} from "@/features/gtm/leadDiscoveryHonesty";
import {
  MARKET_SIZING_HONESTY,
  MARKET_SIZING_NON_GOALS,
} from "@/features/gtm/marketSizingHonesty";

/**
 * FE-S11-03b — Tip GTM Intelligence hub (market sizing + lead discovery).
 * No invented APIs. ICP / territories not linked. Not Production GO / RAG GO.
 */
export function GtmHub() {
  return (
    <div className="space-y-4" data-testid="gtm-hub">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="gtm-hub-honesty"
      >
        Tip GTM pages only: market-sizing + lead-discovery. Live 141221 Postgres
        / live ERP / ICP Engine / territories Studio not claimed. Not Production
        GO / RAG GO.
      </p>

      <ul className="space-y-3">
        <li
          className="rounded border border-[var(--border-default)] p-4"
          data-testid="gtm-hub-market-sizing"
        >
          <Link
            href="/gtm/market-sizing"
            className="text-base font-semibold text-[var(--text-primary)] underline"
          >
            Market Sizing (TAM / SAM / SOM)
          </Link>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {MARKET_SIZING_HONESTY} Non-goals:{" "}
            {MARKET_SIZING_NON_GOALS.slice(0, 2).join("; ")}.
          </p>
        </li>
        <li
          className="rounded border border-[var(--border-default)] p-4"
          data-testid="gtm-hub-lead-discovery"
        >
          <Link
            href="/gtm/lead-discovery"
            className="text-base font-semibold text-[var(--text-primary)] underline"
          >
            Lead Discovery
          </Link>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {LEAD_DISCOVERY_HONESTY} Non-goals:{" "}
            {LEAD_DISCOVERY_NON_GOALS.slice(0, 2).join("; ")}.
          </p>
        </li>
      </ul>
    </div>
  );
}
