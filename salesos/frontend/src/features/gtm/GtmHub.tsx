"use client";

import Link from "next/link";
import {
  ENRICHMENT_HONESTY,
  ENRICHMENT_NON_GOALS,
} from "@/features/gtm/enrichmentHonesty";
import {
  LEAD_DISCOVERY_HONESTY,
  LEAD_DISCOVERY_NON_GOALS,
} from "@/features/gtm/leadDiscoveryHonesty";
import {
  MARKET_SIZING_HONESTY,
  MARKET_SIZING_NON_GOALS,
} from "@/features/gtm/marketSizingHonesty";
import {
  VERIFICATION_HONESTY,
  VERIFICATION_NON_GOALS,
} from "@/features/gtm/verificationHonesty";

/**
 * Tip GTM Intelligence hub (FE-S11-03b + 01/05/06).
 * Tip pages only. Territories not linked. Not Production GO / RAG GO.
 */
export function GtmHub() {
  return (
    <div className="space-y-4" data-testid="gtm-hub">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="gtm-hub-honesty"
      >
        Tip GTM pages only: ICP profiles, market-sizing, lead-discovery,
        enrichment, verification — with tip query-param handoffs between them.
        Live 141221 Postgres / live ERP / territories Studio / lookalikes not
        claimed. Not Production GO / RAG GO.
      </p>

      <ul className="space-y-3">
        <li
          className="rounded border border-[var(--border-default)] p-4"
          data-testid="gtm-hub-icp"
        >
          <Link
            href="/gtm/icp"
            className="text-base font-semibold text-[var(--text-primary)] underline"
          >
            ICP Profiles
          </Link>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            Tip versioned ICPProfile + deterministic score — no ML backtest /
            live 141221 claim.
          </p>
        </li>
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
        <li
          className="rounded border border-[var(--border-default)] p-4"
          data-testid="gtm-hub-enrichment"
        >
          <Link
            href="/gtm/enrichment"
            className="text-base font-semibold text-[var(--text-primary)] underline"
          >
            Enrichment Waterfall
          </Link>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {ENRICHMENT_HONESTY} Non-goals:{" "}
            {ENRICHMENT_NON_GOALS.slice(0, 2).join("; ")}.
          </p>
        </li>
        <li
          className="rounded border border-[var(--border-default)] p-4"
          data-testid="gtm-hub-verification"
        >
          <Link
            href="/gtm/verification"
            className="text-base font-semibold text-[var(--text-primary)] underline"
          >
            Contact Verification
          </Link>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {VERIFICATION_HONESTY} Non-goals:{" "}
            {VERIFICATION_NON_GOALS.slice(0, 2).join("; ")}.
          </p>
        </li>
      </ul>
    </div>
  );
}
