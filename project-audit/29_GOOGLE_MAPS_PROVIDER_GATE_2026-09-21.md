# 29 — Google Maps lead-source and provider gate — 2026-09-21

## Decision

**BLOCK Google Maps scraping and Places-derived lead-list ingestion into SalesOS.** The current standalone Google Maps Scraper Kit is not an approved SalesOS discovery/enrichment provider. Keep the SalesOS path closed unless the intended use is covered by written permission or a separate agreement and a product/legal review confirms the exact data flow.

This is a product and engineering gate based on Google's published terms, not legal advice. The terms may differ for EEA billing accounts or a negotiated/reseller agreement; the applicable account agreement must be checked before any future exception.

## Evidence from the current repository

- [Google Maps Scraper Kit README](../business/google-maps-scraper-kit/README.md) says the kit scrapes Maps business listings and writes a lead list containing names, addresses, phones, websites, ratings, review counts, and optional emails. It describes CSV/JSON outputs and a future integration into SalesOS.
- The same README acknowledges that scraping Maps is against Google's Terms, yet the operational advice says to use proxies for large/repeated jobs. That advice does not make the activity permitted and can encourage bypassing access controls. Do not use the kit for SalesOS lead generation or import its outputs into the Master Data/Fact Review path.
- SalesOS Agent Reach's channel enum and ResearchRequest allowlist do not include google_maps. test_agent_reach_security.py already rejects google_maps as an unknown research channel. This turn adds an explicit regression case to the Fact Proposal evidence classifier so persisted evidence with channel google_maps cannot pass as an Agent Reach source.
- No Maps endpoint/provider was called. After this source gate, a separate provider-spend migration was applied only to `salesos_test`; no production database, browser, staging, or deployment state was changed. See [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md).

## Evidence from current published Google requirements

- The current [Google Maps Platform Terms of Service](https://cloud.google.com/maps-platform/terms), §3.2.3(a), prohibits scraping Maps content for use outside Maps. Its examples explicitly include prefetching, indexing, storing or rehosting Maps content, bulk downloading places information, and copying or saving business names and addresses.
- The same terms, §3.2.3(d)(iii), prohibit using Maps Core Services in a listings or directory service or to create or augment an advertising product. A SalesOS workflow whose purpose is to create and retain prospect lists is close enough to this boundary that it must remain disabled absent written clearance.
- [Places API policies](https://developers.google.com/maps/documentation/places/web-service/policies) say Places content must not be prefetched, cached, or stored beyond listed exceptions. place_id is explicitly exempt and may be stored indefinitely; that exception does not permit storing the associated company name, address, phone, website, rating, or review data as a durable SalesOS lead record.
- Places results also have attribution and display requirements. A Places API call is not a compliant replacement for scraping if its output is still copied into SalesOS' persistent lead database.
- [Places pricing](https://developers.google.com/maps/billing-and-pricing/pricing) and [usage/billing rules](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing) are SKU/field-mask dependent. Any future, permitted map UI needs a verified current rate card, field masks, shared billing-account cap, and pre-call spend reservation. Budget enforcement alone does not grant data-use permission.

## Approved direction for SalesOS

1. Keep the Google Maps scraper and Places results outside the SalesOS master company/person tables, enrichment ledger, review evidence snapshots, exports, and CRM sync.
2. Use company registries, company-owned websites, and B2B data providers whose contract explicitly permits the intended discovery, retention, enrichment, and downstream CRM use. Store source and terms/provenance for each value.
3. If SalesOS later needs a genuine end-user map feature, review it as a separate Maps UI use case with Google Map display, attribution, restricted transient result handling, and an approved agreement. Do not frame it as a bulk lead-generation connector.
4. Before enabling any paid discovery/enrichment source, implement an atomic durable spend reservation that enforces both per-tenant and shared billing-account limits, persists a versioned maximum-price basis, settles actual charges idempotently, and holds uncertain timeouts as reserved until reconciled. Existing hourly UsageMeter rollups are not a real-time spend gate.
5. Do not provision the Minder service principal or invoke a provider until the price card/contract, budget limits, source-to-value validation, and operational owner are recorded.

## Roadmap and status

Focused unit/security regression at the source-gate checkpoint: **60/60 passed**. The later combined Agent Reach/provider-spend unit regression is **79/79 passed**; see [report 30](30_PROVIDER_SPEND_BUDGET_GATE_2026-09-21.md). This closes a research and source-classification gate only. It does not enable Agent Reach providers, create new leads, or unblock Phase 7.

- Roadmap remains **46%** (52/113 last complete census; no new census).
- Phase 7 remains **BLOCKED** on human review, DI method confirmation, and Product/PO sign-off.
- Production remains **NOT APPROVED**.
- Durable provider spend reservation infrastructure has now been implemented and verified only on `salesos_test`; no prices or limits are provisioned and no providers are enabled. Revisit Maps only after written use-case clearance; do not use the scraper as a workaround.

